import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app.api import deps
from app.core.scope import apply_scope
from app.models.domain import Contact, Customer, Employee
from app.schemas.customer import ContactCreate, ContactUpdate, ContactResponse
from app.core.audit import log_action
from app.core.pagination import paginate_query

router = APIRouter()

ALLOWED_CONTACT_SORT_FIELDS = ["id", "name", "email", "phone", "designation", "status"]

def _get_customer_company_id(db: Session, customer_id: int, fallback_user: Employee) -> int:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer and customer.assigned_employee_id:
        emp = db.query(Employee).filter(Employee.id == customer.assigned_employee_id).first()
        if emp and emp.company_id:
            return emp.company_id
    return fallback_user.company_id

@router.post("/", response_model=ContactResponse)
def create_contact(
    *,
    db: Session = Depends(deps.get_db),
    contact_in: ContactCreate,
    request: Request,
    auth_info: dict = Depends(deps.PermissionChecker("Contact", "Create")),
):
    if contact_in.email and contact_in.customer_id:
        company_id = _get_customer_company_id(db, contact_in.customer_id, auth_info["user"])
        existing = (
            db.query(Contact)
            .join(Customer, Contact.customer_id == Customer.id)
            .join(Employee, Customer.assigned_employee_id == Employee.id)
            .filter(
                Employee.company_id == company_id,
                Contact.email == contact_in.email.strip()
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Contact with this email already exists in this company.")

    db_contact = Contact(**contact_in.model_dump())
    db.add(db_contact)
    db.flush()
    
    log_action(
        db,
        auth_info["user"].id,
        "Create",
        "Contact",
        db_contact.id,
        new_val={"name": db_contact.name, "email": db_contact.email, "customer_id": db_contact.customer_id},
        request=request
    )
    db.commit()
    db.refresh(db_contact)
    return db_contact

@router.get("/")
def get_contacts(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    customer_id: Optional[int] = None,
    sort_by: Optional[str] = "name",
    sort_dir: Optional[str] = "asc",
    paginate: bool = True,
    raw: bool = False,
    auth_info: dict = Depends(deps.PermissionChecker("Contact", "View")),
):
    query = apply_scope(db.query(Contact), Contact, auth_info, db)
            
    if search:
        query = query.filter(Contact.name.contains(search) | Contact.email.contains(search))
    if customer_id:
        query = query.filter(Contact.customer_id == customer_id)
        
    return paginate_query(
        query=query,
        model=Contact,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
        allowed_sort_fields=ALLOWED_CONTACT_SORT_FIELDS,
        default_sort_field="name",
        default_sort_dir="asc",
        paginate=paginate,
        raw=raw,
    )

@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(
    contact_id: int,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Contact", "View")),
):
    contact = apply_scope(db.query(Contact).filter(Contact.id == contact_id), Contact, auth_info, db).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    *,
    db: Session = Depends(deps.get_db),
    contact_id: int,
    contact_in: ContactUpdate,
    request: Request,
    auth_info: dict = Depends(deps.PermissionChecker("Contact", "Edit")),
):
    contact = apply_scope(db.query(Contact).filter(Contact.id == contact_id), Contact, auth_info, db).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    update_data = contact_in.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] and update_data["email"] != contact.email:
        company_id = _get_customer_company_id(db, contact.customer_id, auth_info["user"])
        existing = (
            db.query(Contact)
            .join(Customer, Contact.customer_id == Customer.id)
            .join(Employee, Customer.assigned_employee_id == Employee.id)
            .filter(
                Employee.company_id == company_id,
                Contact.email == update_data["email"].strip(),
                Contact.id != contact_id
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Contact with this email already exists in this company.")

    old_vals = {}
    new_vals = {}
    for field, value in update_data.items():
        curr_val = getattr(contact, field)
        if curr_val != value:
            old_vals[field] = curr_val
            new_vals[field] = value
            setattr(contact, field, value)
        
    log_action(
        db,
        auth_info["user"].id,
        "Edit",
        "Contact",
        contact.id,
        old_val=old_vals,
        new_val=new_vals,
        request=request
    )
    db.commit()
    db.refresh(contact)
    return contact

@router.delete("/{contact_id}")
def delete_contact(
    *,
    db: Session = Depends(deps.get_db),
    contact_id: int,
    request: Request,
    auth_info: dict = Depends(deps.PermissionChecker("Contact", "Delete")),
):
    contact = apply_scope(db.query(Contact).filter(Contact.id == contact_id), Contact, auth_info, db).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
        
    log_action(
        db,
        auth_info["user"].id,
        "Delete",
        "Contact",
        contact_id,
        old_val={"name": contact.name, "email": contact.email},
        request=request
    )
    db.delete(contact)
    db.commit()
    return {"message": "Contact deleted successfully"}
