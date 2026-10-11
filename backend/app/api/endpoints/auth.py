from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.google_auth import verify_google_id_token
from app.models.domain import Employee
from app.schemas.employee import Token, GoogleAuthRequest, GoogleAuthResponse

router = APIRouter()

@router.post("/login", response_model=Token)
def login_access_token(db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """OAuth2 compatible token login, get an access token for future requests"""
    user = db.query(Employee).filter(Employee.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if user.status != "Active":
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(user.id, expires_delta=access_token_expires),
        "token_type": "bearer",
    }

@router.post("/google", response_model=GoogleAuthResponse)
def login_google(
    payload: GoogleAuthRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Secure Google OpenID Connect ID token verification and onboarding endpoint.
    - Cryptographically validates token signature, issuer, audience, and email_verified.
    - Protects against account takeover: does not auto-merge with existing password accounts.
    - Quarantines new Google users with status 'Pending_Approval' and zero permissions.
    """
    # 1. Cryptographically verify Google ID Token
    google_data = verify_google_id_token(payload.id_token)
    google_sub = str(google_data["sub"])
    google_email = google_data["email"].lower().strip()
    google_name = google_data.get("name") or google_email.split("@")[0]

    # 2. Check if a user with this google_sub already exists
    # If the column google_sub exists on Employee, query by it, otherwise fallback check by email
    user = None
    if hasattr(Employee, "google_sub"):
        user = db.query(Employee).filter(Employee.google_sub == google_sub).first()

    # 3. If not found by google_sub, check if an existing account has this email
    if not user:
        existing_email_user = db.query(Employee).filter(Employee.email == google_email).first()
        if existing_email_user:
            # Security Rule: Never auto-merge without prior password verification
            if existing_email_user.password_hash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists with password login. Please sign in with your email and password first."
                )
            # If the user has no password_hash and was previously created, link the google_sub
            user = existing_email_user
            if hasattr(user, "google_sub"):
                user.google_sub = google_sub
                db.commit()
                db.refresh(user)

    # 4. If user still does not exist, create a new quarantined Employee
    if not user:
        new_user_kwargs = {
            "name": google_name,
            "email": google_email,
            "status": "Pending_Approval",
            "role_id": None,
            "company_id": None,
            "password_hash": None,
        }
        if hasattr(Employee, "google_sub"):
            new_user_kwargs["google_sub"] = google_sub
        if hasattr(Employee, "auth_provider"):
            new_user_kwargs["auth_provider"] = "google"

        user = Employee(**new_user_kwargs)
        db.add(user)
        db.commit()
        db.refresh(user)

    # 5. Check user status for gating
    if user.status != "Active":
        return {
            "status": "Pending_Approval",
            "message": "Your account is pending administrator approval. Company and role assignment are required before accessing workspace.",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "status": user.status,
            }
        }

    # 6. Active approved user: Issue standard CRM360 JWT
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "status": "Active",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role_id": user.role_id,
            "role_name": user.role.name if user.role else None,
            "status": user.status,
        }
    }

@router.get("/me")
def read_users_me(current_user: Employee = Depends(deps.get_current_active_user)) -> Any:
    """Get current user."""
    perms = []
    if current_user.role:
        if current_user.role.name == "System Administrator":
            perms.append({"module": "Admin", "action": "All"})
        for p in current_user.role.permissions:
            perms.append({"module": p.module, "action": p.action, "scope": p.data_scope})
    
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role_id": current_user.role_id,
        "role_name": current_user.role.name if current_user.role else None,
        "permissions": perms
    }
