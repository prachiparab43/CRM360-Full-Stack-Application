from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.core import security
from app.db.session import SessionLocal
from app.models.domain import Employee, Role, RolePermission
from app.schemas.employee import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"/api/auth/login")

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)) -> Employee:
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = db.query(Employee).filter(Employee.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_active_user(current_user: Employee = Depends(get_current_user)) -> Employee:
    if current_user.status != "Active":
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

class PermissionChecker:
    def __init__(self, module: str, action: str):
        self.module = module
        self.action = action
        
    def __call__(self, current_user: Employee = Depends(get_current_active_user), db: Session = Depends(get_db)):
        if current_user.role and current_user.role.name == "System Administrator":
            return {"user": current_user, "scope": "All"}
            
        perm = db.query(RolePermission).filter(
            RolePermission.role_id == current_user.role_id,
            RolePermission.module == self.module,
            RolePermission.action == self.action
        ).first()
        
        if not perm:
            raise HTTPException(status_code=403, detail=f"Not authorized to {self.action} in {self.module}")
        
        return {"user": current_user, "scope": perm.data_scope}
