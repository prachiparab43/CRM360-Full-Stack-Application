from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.audit import log_action
from app.models.domain import Employee
from app.schemas.employee import Token, RegisterRequest, RegisterResponse

router = APIRouter()

@router.post("/login", response_model=Token)
def login_access_token(
    request: Request,
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """OAuth2 compatible token login, get an access token for future requests"""
    client_ip = request.client.host if request and request.client else "unknown"
    rate_limit_key = f"{client_ip}:{form_data.username}"
    security.check_login_rate_limit(rate_limit_key)

    user = db.query(Employee).filter(Employee.email == form_data.username.lower().strip()).first()
    if not user or not security.verify_password(form_data.password, user.password_hash):
        log_action(
            db=db,
            user_id=user.id if user else None,
            action="Login Failed",
            module="Auth",
            record_id=user.id if user else 0,
            new_val=f"Failed login attempt for {form_data.username}",
            request=request
        )
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    if user.status != "Active":
        log_action(
            db=db,
            user_id=user.id,
            action="Login Blocked",
            module="Auth",
            record_id=user.id,
            new_val=f"Inactive/Pending account: {user.status}",
            request=request
        )
        if user.status in ["Pending_Approval", "Pending"]:
            raise HTTPException(
                status_code=403, 
                detail="Your account has been registered and is pending administrator approval. Please wait for company workspace and role assignment."
            )
        raise HTTPException(status_code=403, detail="Inactive account. Please contact your system administrator.")
    
    log_action(
        db=db,
        user_id=user.id,
        action="Login Success",
        module="Auth",
        record_id=user.id,
        new_val="User logged in",
        request=request
    )

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(user.id, expires_delta=access_token_expires),
        "token_type": "bearer",
        "status": user.status,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "status": user.status,
            "role_id": user.role_id,
            "role_name": user.role.name if user.role else None,
            "company_id": user.company_id,
            "company_name": user.company.name if user.company else None,
        }
    }

@router.post("/register", response_model=RegisterResponse)
def register_user(
    request: Request,
    payload: RegisterRequest,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Public self-registration for new users using email and password.
    - Validates email format and uniqueness.
    - Enforces password complexity policy (minimum 8 characters, letters and digits).
    - Confirms matching passwords.
    - Creates quarantined account with status 'Pending_Approval', company_id=None, role_id=None.
    - Disallows self-assignment of administrative privileges or roles.
    """
    clean_email = str(payload.email).lower().strip()
    clean_name = payload.name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Full name is required.")
    
    if payload.confirm_password and payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    
    security.validate_password_policy(payload.password)
    
    existing = db.query(Employee).filter(Employee.email == clean_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email address already exists.")
    
    new_user = Employee(
        name=clean_name,
        email=clean_email,
        phone=payload.phone.strip() if payload.phone else None,
        password_hash=security.get_password_hash(payload.password),
        status="Pending_Approval",
        role_id=None,
        company_id=None,
        auth_provider="local"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    log_action(
        db=db,
        user_id=new_user.id,
        action="New Registration",
        module="Auth",
        record_id=new_user.id,
        new_val={"name": new_user.name, "email": new_user.email, "status": new_user.status},
        request=request
    )
    
    return {
        "message": "Account created successfully. Your account is pending administrator approval and workspace assignment.",
        "status": "Pending_Approval",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "status": new_user.status,
        }
    }

@router.get("/me")
def read_users_me(
    current_user: Employee = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """Get current authenticated user, permissions, and workspace details."""
    perms = []
    if current_user.status == "Active" and current_user.role and current_user.role.status == "Active":
        for p in current_user.role.permissions:
            perms.append({"module": p.module, "action": p.action, "scope": p.data_scope})
    
    company_name = None
    if current_user.company:
        company_name = current_user.company.name

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone,
        "department": current_user.department,
        "designation": current_user.designation,
        "status": current_user.status,
        "role_id": current_user.role_id,
        "role_name": current_user.role.name if current_user.role else None,
        "company_id": current_user.company_id,
        "company_name": company_name,
        "manager_id": current_user.manager_id,
        "permissions": perms
    }
