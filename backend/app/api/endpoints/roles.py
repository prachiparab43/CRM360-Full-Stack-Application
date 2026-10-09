from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from app.api import deps
from app.models.domain import Role, RolePermission, Employee
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse
from app.core.audit import log_action

router = APIRouter()

@router.post("/", response_model=RoleResponse)
def create_role(
    *,
    db: Session = Depends(deps.get_db),
    role_in: RoleCreate,
    auth_info: dict = Depends(deps.PermissionChecker("Role", "Create")),
):
    db_role = Role(name=role_in.name, description=role_in.description, status=role_in.status)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    
    for perm in role_in.permissions:
        db_perm = RolePermission(
            role_id=db_role.id, 
            module=perm.module, 
            action=perm.action, 
            data_scope=perm.data_scope
        )
        db.add(db_perm)
    db.commit()
    db.refresh(db_role)
    
    log_action(db, auth_info["user"].id, "Create", "Role", db_role.id, new_val=role_in.name)
    return db_role

@router.get("/", response_model=List[RoleResponse])
def get_roles(
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Role", "View")),
):
    return db.query(Role).all()

@router.get("/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: int,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Role", "View")),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.post("/{role_id}/assign", response_model=dict)
def assign_role(
    role_id: int,
    employee_id: int,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Role", "Assign")),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
        
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    old_role = employee.role_id
    employee.role_id = role.id
    db.commit()
    
    log_action(db, auth_info["user"].id, "Assign Role", "Employee", employee.id, old_val=str(old_role), new_val=str(role.id))
    return {"message": "Role assigned successfully"}
@router.put("/{role_id}", response_model=RoleResponse)
def update_role(
    *,
    db: Session = Depends(deps.get_db),
    role_id: int,
    role_in: RoleUpdate,
    auth_info: dict = Depends(deps.PermissionChecker("Role", "Edit")),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
        
    update_data = role_in.model_dump(exclude_unset=True, exclude={"permissions"})
    for field, value in update_data.items():
        setattr(role, field, value)
        
    if role_in.permissions is not None:
        db.query(RolePermission).filter(RolePermission.role_id == role.id).delete()
        for perm in role_in.permissions:
            db_perm = RolePermission(
                role_id=role.id, 
                module=perm.module, 
                action=perm.action, 
                data_scope=perm.data_scope
            )
            db.add(db_perm)
            
    db.commit()
    db.refresh(role)
    
    log_action(db, auth_info["user"].id, "Edit", "Role", role.id)
    return role
