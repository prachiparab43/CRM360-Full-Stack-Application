import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app.api import deps
from app.core.scope import apply_scope
from app.models.domain import Customer, Employee
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.core.audit import log_action
from app.core.pagination import paginate_query

router = APIRouter()

ALLOWED_CUSTOMER_SORT_FIELDS = ["id", "name", "email", "phone", "industry", "status"]

def _get_target_company_id(db: Session, employee_id: Optional[int], fallback_user: Employee) -> int:
    if employee_id:
        emp = db.query(Employee).filter(Employee.id == employee_id).first()
        if emp and emp.company_id:
            return emp.company_id
    return fallback_user.company_id

@router.post("/", response_model=CustomerResponse)
def create_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_in: CustomerCreate,
    request: Request,
    auth_info: dict = Depends(deps.PermissionChecker("Customer", "Create")),
):
    target_company_id = _get_target_company_id(db, customer_in.assigned_employee_id, auth_info["user"])
    
    # Unique customer name per company
    existing = (
        db.query(Customer)
        .outerjoin(Employee, Customer.assigned_employee_id == Employee.id)
        .filter(
            (Employee.company_id == target_company_id) | (Customer.assigned_employee_id.is_(None)),
            Customer.name == customer_in.name
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Customer with this name already exists in this company.")
        
    customer_data = customer_in.model_dump()
    if not customer_data.get("assigned_employee_id"):
        customer_data["assigned_employee_id"] = auth_info["user"].id

    db_customer = Customer(**customer_data)
    db.add(db_customer)
    db.flush()
    
    log_action(
        db,
        auth_info["user"].id,
        "Create",
        "Customer",
        db_customer.id,
        new_val={"name": db_customer.name, "email": db_customer.email},
        request=request
    )
    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.get("/")
def get_customers(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: Optional[str] = "name",
    sort_dir: Optional[str] = "asc",
    paginate: bool = True,
    raw: bool = False,
    auth_info: dict = Depends(deps.PermissionChecker("Customer", "View")),
):
    query = apply_scope(db.query(Customer), Customer, auth_info, db)
        
    if search:
        query = query.filter(Customer.name.contains(search) | Customer.email.contains(search))
    if status:
        query = query.filter(Customer.status == status)
        
    return paginate_query(
        query=query,
        model=Customer,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
        allowed_sort_fields=ALLOWED_CUSTOMER_SORT_FIELDS,
        default_sort_field="name",
        default_sort_dir="asc",
        paginate=paginate,
        raw=raw,
    )

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Customer", "View")),
):
    customer = apply_scope(db.query(Customer).filter(Customer.id == customer_id), Customer, auth_info, db).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
    customer_in: CustomerUpdate,
    request: Request,
    auth_info: dict = Depends(deps.PermissionChecker("Customer", "Edit")),
):
    customer = apply_scope(db.query(Customer).filter(Customer.id == customer_id), Customer, auth_info, db).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = customer_in.model_dump(exclude_unset=True)

    # Check unique name per company if name is changed
    if "name" in update_data and update_data["name"] != customer.name:
        target_emp_id = update_data.get("assigned_employee_id", customer.assigned_employee_id)
        target_company_id = _get_target_company_id(db, target_emp_id, auth_info["user"])
        existing = (
            db.query(Customer)
            .join(Employee, Customer.assigned_employee_id == Employee.id)
            .filter(
                Employee.company_id == target_company_id,
                Customer.name == update_data["name"],
                Customer.id != customer_id
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Customer with this name already exists in this company.")

    old_assigned = customer.assigned_employee_id
    old_vals = {}
    new_vals = {}
    for field, value in update_data.items():
        curr_val = getattr(customer, field)
        if curr_val != value:
            old_vals[field] = curr_val
            new_vals[field] = value
            setattr(customer, field, value)
        
    action_name = "Reassign" if ("assigned_employee_id" in update_data and update_data["assigned_employee_id"] != old_assigned) else "Edit"
    log_action(
        db,
        auth_info["user"].id,
        action_name,
        "Customer",
        customer.id,
        old_val=old_vals,
        new_val=new_vals,
        request=request
    )
    db.commit()
    db.refresh(customer)
    return customer
