from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
import json

from app.api import deps
from app.models.domain import Role, RolePermission, Employee, AuditLog
from app.schemas.role import (
    RoleCreate, RoleUpdate, RoleResponse,
    RoleCatalogResponse, PermissionHistoryItem
)
from app.core.audit import log_action
from app.core.permissions import is_valid_permission, get_catalog, SCOPE_RANK
from app.core.scope import apply_scope

router = APIRouter()

def validate_permissions_list(permissions):
    """Validate that every permission matches the official RBAC catalog."""
    if not permissions:
        return
    for p in permissions:
        if not is_valid_permission(p.module, p.action, p.data_scope):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid permission: module '{p.module}', action '{p.action}', scope '{p.data_scope}' is not valid in the catalog."
            )

def caller_can_assign_role(caller: Employee, target_role: Role) -> bool:
    """Anti-escalation check: caller must hold all permissions of target_role with at least equal scope."""
    if not caller.role:
        return False
    caller_perms = {
        (p.module, p.action): p.data_scope
        for p in caller.role.permissions
    }
    for tp in target_role.permissions:
        caller_scope = caller_perms.get((tp.module, tp.action))
        if not caller_scope:
            return False
        if SCOPE_RANK.get(caller_scope, 0) < SCOPE_RANK.get(tp.data_scope, 0):
            return False
    return True

def would_remove_last_role_admin(db: Session, affected_role_id: int) -> bool:
    """Check if modifying or deactivating affected_role_id leaves zero active employees with Role:Edit or Role:Assign."""
    admin_perms = db.query(RolePermission.role_id).filter(
        RolePermission.module == "Role",
        RolePermission.action.in_(["Edit", "Assign"])
    ).distinct().all()
    admin_role_ids = {r[0] for r in admin_perms}
    if affected_role_id not in admin_role_ids:
        return False

    active_admins = db.query(Employee).filter(
        Employee.status == "Active",
        Employee.role_id.in_(admin_role_ids)
    ).all()
    other_admins = [e for e in active_admins if e.role_id != affected_role_id]
    return len(other_admins) == 0

@router.get("/catalog", response_model=RoleCatalogResponse)
def get_roles_catalog(
    auth_info: dict = Depends(deps.PermissionChecker("Role", "View")),
):
    """Returns the full permission catalog including valid modules, actions, and scopes."""
    return get_catalog()

@router.post("/", response_model=RoleResponse)
def create_role(
    *,
    db: Session = Depends(deps.get_db),
    role_in: RoleCreate,
    auth_info: dict = Depends(deps.PermissionChecker("Role", "Create")),
):
    # Check duplicate name (409)
    name_clean = role_in.name.strip()
    existing = db.query(Role).filter(func.lower(Role.name) == name_clean.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A role with this name already exists"
        )

    # Validate permissions (422)
    validate_permissions_list(role_in.permissions)

    db_role = Role(
        name=name_clean,
        description=role_in.description,
        status=role_in.status or "Active",
        is_system=False
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)

    perms_created = []
    for perm in (role_in.permissions or []):
        db_perm = RolePermission(
            role_id=db_role.id,
            module=perm.module,
            action=perm.action,
            data_scope=perm.data_scope
        )
        db.add(db_perm)
        perms_created.append({"module": perm.module, "action": perm.action, "scope": perm.data_scope})

    log_action(
        db,
        auth_info["user"].id,
        "Create",
        "Role",
        db_role.id,
        old_val=None,
        new_val=json.dumps(perms_created)
    )
    db.commit()
    db.refresh(db_role)
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

    # Block editing/deactivating roles with is_system
    if role.is_system:
        raise HTTPException(
            status_code=400,
            detail="System role cannot be modified or deactivated."
        )

    # Check duplicate name (409)
    if role_in.name:
        name_clean = role_in.name.strip()
        if name_clean.lower() != role.name.lower():
            existing = db.query(Role).filter(
                func.lower(Role.name) == name_clean.lower(),
                Role.id != role.id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A role with this name already exists"
                )
            role.name = name_clean

    # Check deactivation
    if role_in.status and role_in.status != "Active":
        if would_remove_last_role_admin(db, role.id):
            raise HTTPException(
                status_code=400,
                detail="Cannot deactivate role: would leave zero active employees with Role management permissions."
            )
        role.status = role_in.status
    elif role_in.status:
        role.status = role_in.status

    if role_in.description is not None:
        role.description = role_in.description

    # Handle permissions update
    if role_in.permissions is not None:
        validate_permissions_list(role_in.permissions)
        
        # Check last role admin removal if new permissions remove Role:Edit/Assign
        if would_remove_last_role_admin(db, role.id):
            has_role_mgmt = any(
                p.module == "Role" and p.action in ["Edit", "Assign"]
                for p in role_in.permissions
            )
            if not has_role_mgmt:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot remove Role management permissions: would leave zero active employees with Role management."
                )

        old_perms = [{"module": p.module, "action": p.action, "scope": p.data_scope} for p in role.permissions]
        db.query(RolePermission).filter(RolePermission.role_id == role.id).delete()
        new_perms = []
        for perm in role_in.permissions:
            db_perm = RolePermission(
                role_id=role.id,
                module=perm.module,
                action=perm.action,
                data_scope=perm.data_scope
            )
            db.add(db_perm)
            new_perms.append({"module": perm.module, "action": perm.action, "scope": perm.data_scope})
            
        log_action(
            db,
            auth_info["user"].id,
            "Edit Permissions",
            "Role",
            role.id,
            old_val=json.dumps(old_perms),
            new_val=json.dumps(new_perms)
        )

    db.commit()
    db.refresh(role)
    return role

@router.post("/{role_id}/activate", response_model=RoleResponse)
def activate_role(
    role_id: int,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Role", "Edit")),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
        
    role.status = "Active"
    log_action(db, auth_info["user"].id, "Activate", "Role", role.id, new_val="Active")
    db.commit()
    db.refresh(role)
    return role

@router.post("/{role_id}/deactivate", response_model=RoleResponse)
def deactivate_role(
    role_id: int,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Role", "Edit")),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
        
    if role.is_system:
        raise HTTPException(status_code=400, detail="System role cannot be deactivated.")
        
    if would_remove_last_role_admin(db, role.id):
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate role: would leave zero active employees with Role management permissions."
        )

    role.status = "Inactive"
    log_action(db, auth_info["user"].id, "Deactivate", "Role", role.id, new_val="Inactive")
    db.commit()
    db.refresh(role)
    return role

@router.delete("/{role_id}", response_model=dict)
def delete_role(
    role_id: int,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Role", "Delete")),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
        
    if role.is_system:
        raise HTTPException(status_code=400, detail="System role cannot be deleted.")
        
    if would_remove_last_role_admin(db, role.id):
        raise HTTPException(
            status_code=400,
            detail="Cannot delete role: would leave zero active employees with Role management permissions."
        )

    assigned_count = db.query(Employee).filter(Employee.role_id == role.id).count()
    if assigned_count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete role with assigned employees.")

    log_action(db, auth_info["user"].id, "Delete", "Role", role_id)
    db.delete(role)
    db.commit()
    return {"message": "Role deleted successfully"}

@router.get("/{role_id}/permission-history", response_model=List[PermissionHistoryItem])
def get_permission_history(
    role_id: int,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Role", "View")),
):
    """Retrieve audit history of permissions changes for a role."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    logs = db.query(AuditLog).filter(
        AuditLog.module == "Role",
        AuditLog.record_id == role_id
    ).order_by(AuditLog.id.desc()).all()

    items = []
    for log in logs:
        old_p = None
        new_p = None
        if log.old_value:
            try:
                old_p = json.loads(log.old_value)
            except Exception:
                old_p = None
        if log.new_value:
            try:
                new_p = json.loads(log.new_value)
            except Exception:
                new_p = None
        items.append({
            "id": log.id,
            "timestamp": log.timestamp,
            "user_id": log.user_id,
            "action": log.action,
            "old_permissions": old_p if isinstance(old_p, list) else None,
            "new_permissions": new_p if isinstance(new_p, list) else None,
        })
    return items

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

    caller = auth_info["user"]
    # Caller must have employee scope over target
    scoped_emp = apply_scope(db.query(Employee).filter(Employee.id == employee_id), Employee, auth_info, db).first()
    if not scoped_emp:
        raise HTTPException(status_code=403, detail="Not authorized to assign role to this employee")

    # Anti-escalation check: caller cannot assign a role holding permissions they lack
    if not caller_can_assign_role(caller, role):
        raise HTTPException(
            status_code=403,
            detail="Cannot assign a role that possesses permissions or scopes you do not possess."
        )

    # Last-admin protection: cannot remove role from the last employee holding Role:Edit/Assign
    if employee.role_id and employee.role_id != role.id:
        has_role_mgmt = db.query(RolePermission).filter(
            RolePermission.role_id == employee.role_id,
            RolePermission.module == "Role",
            RolePermission.action.in_(["Edit", "Assign"])
        ).first() is not None
        if has_role_mgmt and employee.status == "Active":
            # Check if other active role admins exist
            admin_roles = db.query(RolePermission.role_id).filter(
                RolePermission.module == "Role",
                RolePermission.action.in_(["Edit", "Assign"])
            ).distinct().all()
            admin_role_ids = {r[0] for r in admin_roles}
            other_active_admins = db.query(Employee).filter(
                Employee.status == "Active",
                Employee.role_id.in_(admin_role_ids),
                Employee.id != employee.id
            ).count()
            target_has_mgmt = any(p.module == "Role" and p.action in ["Edit", "Assign"] for p in role.permissions)
            if other_active_admins == 0 and not target_has_mgmt:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot reassign the last employee with Role management permissions."
                )

    old_role = employee.role_id
    employee.role_id = role.id
    db.commit()
    
    log_action(db, caller.id, "Assign Role", "Employee", employee.id, old_val=str(old_role), new_val=str(role.id))
    return {"message": "Role assigned successfully"}
