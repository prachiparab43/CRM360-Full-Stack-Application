from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.models.domain import Employee, Company, Role
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.core.audit import log_action
from app.core.security import get_password_hash

router = APIRouter()

@router.post("/", response_model=EmployeeResponse)
def create_employee(
    *,
    db: Session = Depends(deps.get_db),
    employee_in: EmployeeCreate,
    auth_info: dict = Depends(deps.PermissionChecker("Employee", "Create")),
):
    if db.query(Employee).filter(Employee.email == employee_in.email).first():
        raise HTTPException(status_code=400, detail="Employee with this email already exists.")
        
    emp_data = employee_in.model_dump()
    password = emp_data.pop("password")
    
    db_employee = Employee(**emp_data, password_hash=get_password_hash(password))
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    
    log_action(db, auth_info["user"].id, "Create", "Employee", db_employee.id, new_val=db_employee.email)
    return db_employee

@router.get("/", response_model=List[EmployeeResponse])
def get_employees(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
    department: Optional[str] = None,
    auth_info: dict = Depends(deps.PermissionChecker("Employee", "View")),
):
    query = db.query(Employee)
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    
    if scope == "Own":
        query = query.filter(Employee.id == curr_user.id)
    elif scope == "Team":
        query = query.filter(Employee.company_id == curr_user.company_id, Employee.department == curr_user.department)
    elif scope == "Company":
        query = query.filter(Employee.company_id == curr_user.company_id)
        
    if search:
        query = query.filter(Employee.name.contains(search) | Employee.email.contains(search))
    if status:
        query = query.filter(Employee.status == status)
    if department:
        query = query.filter(Employee.department == department)
        
    return query.order_by(Employee.name).offset(skip).limit(limit).all()

@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    *,
    db: Session = Depends(deps.get_db),
    employee_id: int,
    employee_in: EmployeeUpdate,
    auth_info: dict = Depends(deps.PermissionChecker("Employee", "Edit")),
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    if scope == "Own" and employee.id != curr_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this employee")
    elif scope == "Company" and employee.company_id != curr_user.company_id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this employee")

    update_data = employee_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        password = update_data.pop("password")
        employee.password_hash = get_password_hash(password)
        
    for field, value in update_data.items():
        setattr(employee, field, value)
        
    db.commit()
    db.refresh(employee)
    log_action(db, auth_info["user"].id, "Edit", "Employee", employee.id)
    return employee
