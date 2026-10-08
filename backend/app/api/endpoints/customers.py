from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.models.domain import Customer, Employee
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.core.audit import log_action

router = APIRouter()

@router.post("/", response_model=CustomerResponse)
def create_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_in: CustomerCreate,
    auth_info: dict = Depends(deps.PermissionChecker("Customer", "Create")),
):
    if db.query(Customer).filter(Customer.name == customer_in.name).first():
        raise HTTPException(status_code=400, detail="Customer with this name already exists.")
        
    db_customer = Customer(**customer_in.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    
    log_action(db, auth_info["user"].id, "Create", "Customer", db_customer.id, new_val=db_customer.name)
    return db_customer

@router.get("/", response_model=List[CustomerResponse])
def get_customers(
    db: Session = Depends(deps.get_db),
    skip: int = 0, limit: int = 100,
    search: Optional[str] = None, status: Optional[str] = None,
    auth_info: dict = Depends(deps.PermissionChecker("Customer", "View")),
):
    query = db.query(Customer)
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    
    if scope == "Own":
        query = query.filter(Customer.assigned_employee_id == curr_user.id)
    elif scope in ["Team", "Company"]:
        query = query.join(Employee, Customer.assigned_employee_id == Employee.id).filter(Employee.company_id == curr_user.company_id)
        
    if search:
        query = query.filter(Customer.name.contains(search) | Customer.email.contains(search))
    if status:
        query = query.filter(Customer.status == status)
        
    return query.order_by(Customer.name).offset(skip).limit(limit).all()

@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
    customer_in: CustomerUpdate,
    auth_info: dict = Depends(deps.PermissionChecker("Customer", "Edit")),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = customer_in.model_dump(exclude_unset=True)
    old_assigned = customer.assigned_employee_id
    
    for field, value in update_data.items():
        setattr(customer, field, value)
        
    db.commit()
    db.refresh(customer)
    
    if "assigned_employee_id" in update_data and update_data["assigned_employee_id"] != old_assigned:
        log_action(db, auth_info["user"].id, "Reassign", "Customer", customer.id, old_val=str(old_assigned), new_val=str(customer.assigned_employee_id))
    else:
        log_action(db, auth_info["user"].id, "Edit", "Customer", customer.id)
        
    return customer
