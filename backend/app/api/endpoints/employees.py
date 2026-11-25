from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.models.domain import Employee, Company, Role, RolePermission
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse, PasswordResetRequest
from app.core.audit import log_action
from app.core.security import get_password_hash, validate_password_policy
from app.core.scope import apply_scope
from app.core.permissions import SCOPE_RANK
from app.core.pagination import paginate_query

router = APIRouter()

ALLOWED_EMPLOYEE_SORT = ["id", "name", "email", "department", "designation", "status", "joining_date"]

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

def is_last_active_role_admin(db: Session, employee_id: int) -> bool:
    """Check if employee_id is the last active employee with Role Edit or Assign permissions."""
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp or not emp.role_id or emp.status != "Active":
        return False
        
    has_mgmt = db.query(RolePermission).filter(
        RolePermission.role_id == emp.role_id,
        RolePermission.module == "Role",
        RolePermission.action.in_(["Edit", "Assign"])
    ).first() is not None
    if not has_mgmt:
        return False

    admin_roles = db.query(RolePermission.role_id).filter(
        RolePermission.module == "Role",
        RolePermission.action.in_(["Edit", "Assign"])
    ).distinct().all()
    admin_role_ids = {r[0] for r in admin_roles}

    other_admins = db.query(Employee).filter(
        Employee.status == "Active",
        Employee.role_id.in_(admin_role_ids),
        Employee.id != employee_id
    ).count()
    return other_admins == 0

@router.post("/", response_model=EmployeeResponse)
def create_employee(
    *,
    db: Session = Depends(deps.get_db),
    employee_in: EmployeeCreate,
    auth_info: dict = Depends(deps.PermissionChecker("Employee", "Create")),
):
    if db.query(Employee).filter(Employee.email == employee_in.email).first():
        raise HTTPException(status_code=400, detail="Employee with this email already exists.")
        
    caller = auth_info["user"]
    scope = auth_info["scope"]

    # Scope check on create
    if scope == "Company":
        if employee_in.company_id and employee_in.company_id != caller.company_id:
            raise HTTPException(status_code=403, detail="Cannot create employee for another company.")
    elif scope == "Own":
        raise HTTPException(status_code=403, detail="Own scope cannot create other employees.")

    # Role assignment anti-escalation & permission check
    target_role = None
    if employee_in.role_id:
        has_assign = db.query(RolePermission).filter(
            RolePermission.role_id == caller.role_id,
            RolePermission.module == "Role",
            RolePermission.action == "Assign"
        ).first() is not None
        if not has_assign:
            raise HTTPException(status_code=403, detail="Role Assign permission required to set employee role.")

        target_role = db.query(Role).filter(Role.id == employee_in.role_id).first()
        if not target_role:
            raise HTTPException(status_code=404, detail="Assigned role not found.")
            
        if not caller_can_assign_role(caller, target_role):
            raise HTTPException(
                status_code=403,
                detail="Cannot assign a role that possesses permissions or scopes you do not possess."
            )

    emp_data = employee_in.model_dump()
    password = emp_data.pop("password")
    confirm_password = emp_data.pop("confirm_password", None)
    if confirm_password and password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
        
    validate_password_policy(password)
    
    # Default company_id if not provided
    if not emp_data.get("company_id") and caller.company_id:
        emp_data["company_id"] = caller.company_id

    db_employee = Employee(**emp_data, password_hash=get_password_hash(password))
    db.add(db_employee)
    db.flush()
    
    action_type = "Create"
    if target_role and (getattr(target_role, "is_system", False) or target_role.name == "System Administrator"):
        action_type = "Create Administrator"
        
    log_action(
        db,
        caller.id,
        action_type,
        "Employee",
        db_employee.id,
        new_val={"name": db_employee.name, "email": db_employee.email, "role": target_role.name if target_role else None, "status": db_employee.status}
    )
    db.commit()
    db.refresh(db_employee)
    return db_employee

@router.get("/")
def get_employees(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
    department: Optional[str] = None,
    role_id: Optional[int] = None,
    sort_by: Optional[str] = "name",
    sort_dir: Optional[str] = "asc",
    paginate: bool = True,
    raw: bool = False,
    auth_info: dict = Depends(deps.PermissionChecker("Employee", "View")),
):
    query = apply_scope(db.query(Employee), Employee, auth_info, db)
        
    if search:
        query = query.filter(Employee.name.contains(search) | Employee.email.contains(search))
    if status:
        query = query.filter(Employee.status == status)
    if department:
        query = query.filter(Employee.department == department)
    if role_id is not None:
        query = query.filter(Employee.role_id == role_id)
        
    res = paginate_query(
        query=query,
        model=Employee,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
        allowed_sort_fields=ALLOWED_EMPLOYEE_SORT,
        default_sort_field="name",
        default_sort_dir="asc",
        paginate=paginate,
        raw=raw,
    )
    if isinstance(res, dict) and "items" in res:
        res["items"] = [EmployeeResponse.model_validate(item) for item in res["items"]]
    elif isinstance(res, list):
        res = [EmployeeResponse.model_validate(item) for item in res]
    return res

@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Employee", "View")),
):
    employee = apply_scope(db.query(Employee).filter(Employee.id == employee_id), Employee, auth_info, db).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    *,
    db: Session = Depends(deps.get_db),
    employee_id: int,
    employee_in: EmployeeUpdate,
    auth_info: dict = Depends(deps.PermissionChecker("Employee", "Edit")),
):
    employee = apply_scope(db.query(Employee).filter(Employee.id == employee_id), Employee, auth_info, db).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found or outside authorized scope")
        
    caller = auth_info["user"]
    update_data = employee_in.model_dump(exclude_unset=True)

    # Check password update policy
    if "password" in update_data:
        password = update_data.pop("password")
        if password:
            validate_password_policy(password)
            employee.password_hash = get_password_hash(password)

    # Check status change: cannot deactivate last role admin
    if "status" in update_data and update_data["status"] != "Active" and employee.status == "Active":
        if is_last_active_role_admin(db, employee.id):
            raise HTTPException(
                status_code=400,
                detail="Cannot deactivate the last active employee holding Role management permissions."
            )

    # Check role change: requires Role:Assign, anti-escalation, and last-admin check
    if "role_id" in update_data and update_data["role_id"] != employee.role_id:
        has_assign = db.query(RolePermission).filter(
            RolePermission.role_id == caller.role_id,
            RolePermission.module == "Role",
            RolePermission.action == "Assign"
        ).first() is not None
        if not has_assign:
            raise HTTPException(status_code=403, detail="Role Assign permission required to change role.")

        new_role_id = update_data["role_id"]
        target_role = db.query(Role).filter(Role.id == new_role_id).first() if new_role_id else None
        if new_role_id and not target_role:
            raise HTTPException(status_code=404, detail="Role not found.")

        if target_role and not caller_can_assign_role(caller, target_role):
            raise HTTPException(
                status_code=403,
                detail="Cannot assign a role that possesses permissions or scopes you do not possess."
            )

        # Check last role admin removal
        if is_last_active_role_admin(db, employee.id):
            target_has_mgmt = target_role and any(
                p.module == "Role" and p.action in ["Edit", "Assign"]
                for p in target_role.permissions
            )
            if not target_has_mgmt:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot change role of the last active employee holding Role management permissions."
                )

    old_vals = {}
    new_vals = {}
    old_status = employee.status
    old_role_id = employee.role_id

    for field, value in update_data.items():
        curr_val = getattr(employee, field)
        if curr_val != value:
            old_vals[field] = curr_val
            new_vals[field] = value
            setattr(employee, field, value)
        
    action_name = "Edit"
    if "status" in update_data and old_status != update_data["status"]:
        if old_status in ["Pending_Approval", "Pending"] and update_data["status"] == "Active":
            action_name = "Account Approval"
        elif update_data["status"] != "Active":
            action_name = "Account Deactivation"
    elif "role_id" in update_data and old_role_id != update_data["role_id"]:
        action_name = "Role Assigned"

    log_action(db, caller.id, action_name, "Employee", employee.id, old_val=old_vals, new_val=new_vals)
    db.commit()
    db.refresh(employee)
    return employee

@router.delete("/{employee_id}", response_model=dict)
def delete_employee(
    employee_id: int,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Employee", "Delete")),
):
    employee = apply_scope(db.query(Employee).filter(Employee.id == employee_id), Employee, auth_info, db).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found or outside authorized scope")

    if is_last_active_role_admin(db, employee.id):
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the last active employee holding Role management permissions."
        )

    db.delete(employee)
    db.commit()
    log_action(db, auth_info["user"].id, "Delete", "Employee", employee_id)
    return {"message": "Employee deleted successfully"}

@router.post("/{employee_id}/reset-password", response_model=dict)
def reset_employee_password(
    *,
    db: Session = Depends(deps.get_db),
    employee_id: int,
    reset_in: PasswordResetRequest,
    auth_info: dict = Depends(deps.PermissionChecker("Employee", "Edit")),
):
    employee = apply_scope(db.query(Employee).filter(Employee.id == employee_id), Employee, auth_info, db).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found or outside authorized scope")

    caller = auth_info["user"]
    if employee.role and not caller_can_assign_role(caller, employee.role):
        raise HTTPException(
            status_code=403,
            detail="Cannot reset password for a user possessing permissions or scopes you do not possess."
        )

    if reset_in.confirm_password and reset_in.password != reset_in.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    validate_password_policy(reset_in.password)
    employee.password_hash = get_password_hash(reset_in.password)

    log_action(
        db,
        caller.id,
        "Password Reset",
        "Employee",
        employee.id,
        new_val={"target_email": employee.email, "reset_by": caller.email}
    )
    db.commit()
    return {"message": f"Password for {employee.email} has been reset successfully."}

@router.post("/{employee_id}/activate", response_model=EmployeeResponse)
def activate_employee(
    employee_id: int,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Employee", "Edit")),
):
    employee = apply_scope(db.query(Employee).filter(Employee.id == employee_id), Employee, auth_info, db).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found or outside authorized scope")
        
    old_status = employee.status
    employee.status = "Active"
    log_action(
        db,
        auth_info["user"].id,
        "Account Activation",
        "Employee",
        employee.id,
        old_val={"status": old_status},
        new_val={"status": "Active"}
    )
    db.commit()
    db.refresh(employee)
    return EmployeeResponse.model_validate(employee)

@router.post("/{employee_id}/deactivate", response_model=EmployeeResponse)
def deactivate_employee(
    employee_id: int,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Employee", "Edit")),
):
    employee = apply_scope(db.query(Employee).filter(Employee.id == employee_id), Employee, auth_info, db).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found or outside authorized scope")

    if is_last_active_role_admin(db, employee.id):
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate the last active employee holding Role management permissions."
        )

    old_status = employee.status
    employee.status = "Inactive"
    log_action(
        db,
        auth_info["user"].id,
        "Account Deactivation",
        "Employee",
        employee.id,
        old_val={"status": old_status},
        new_val={"status": "Inactive"}
    )
    db.commit()
    db.refresh(employee)
    return EmployeeResponse.model_validate(employee)

