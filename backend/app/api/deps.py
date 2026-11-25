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
        if token_data.sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(Employee).filter(Employee.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def get_current_active_user(current_user: Employee = Depends(get_current_user)) -> Employee:
    if current_user.status != "Active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive or pending approval user")
    return current_user

class PermissionChecker:
    def __init__(self, module: str, action: str):
        self.module = module
        self.action = action
        
    def __call__(self, current_user: Employee = Depends(get_current_active_user), db: Session = Depends(get_db)):
        if current_user.status != "Active":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
            
        if not current_user.role or current_user.role.status != "Active":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role is inactive or unassigned")
            
        module_name = "Geo" if self.module == "GeoTracking" else self.module
        
        perms = db.query(RolePermission).filter(
            RolePermission.role_id == current_user.role_id,
            RolePermission.module.in_([module_name, self.module])
        ).all()
        
        target_perm = None
        for p in perms:
            if p.action == self.action:
                target_perm = p
                break
            if module_name == "Geo" and self.action == "View" and p.action in ["Geo.ViewLiveLocation", "View"]:
                target_perm = p
                break
                
        if not target_perm:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to {self.action} in {self.module}")
            
        return {"user": current_user, "scope": target_perm.data_scope}
