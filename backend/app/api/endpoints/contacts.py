from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.models.domain import Contact, Customer, Employee
from app.schemas.customer import ContactCreate, ContactUpdate, ContactResponse
from app.core.audit import log_action

router = APIRouter()

@router.post("/", response_model=ContactResponse)
def create_contact(
    *,
    db: Session = Depends(deps.get_db),
    contact_in: ContactCreate,
    auth_info: dict = Depends(deps.PermissionChecker("Contact", "Create")),
):
    db_contact = Contact(**contact_in.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    
    log_action(db, auth_info["user"].id, "Create", "Contact", db_contact.id, new_val=db_contact.name)
    return db_contact

@router.get("/", response_model=List[ContactResponse])
def get_contacts(
    db: Session = Depends(deps.get_db),
    skip: int = 0, limit: int = 100,
    search: Optional[str] = None, customer_id: Optional[int] = None,
    auth_info: dict = Depends(deps.PermissionChecker("Contact", "View")),
):
    query = db.query(Contact)
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    
    if scope in ["Own", "Team", "Company"]:
        # Match contacts via their linked customer's assigned employee
        query = query.join(Customer, Contact.customer_id == Customer.id).join(Employee, Customer.assigned_employee_id == Employee.id)
        if scope == "Own":
            query = query.filter(Customer.assigned_employee_id == curr_user.id)
        else:
            query = query.filter(Employee.company_id == curr_user.company_id)
            
    if search:
        query = query.filter(Contact.name.contains(search) | Contact.email.contains(search))
    if customer_id:
        query = query.filter(Contact.customer_id == customer_id)
        
    return query.order_by(Contact.name).offset(skip).limit(limit).all()

@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    *,
    db: Session = Depends(deps.get_db),
    contact_id: int,
    contact_in: ContactUpdate,
    auth_info: dict = Depends(deps.PermissionChecker("Contact", "Edit")),
):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    update_data = contact_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)
        
    db.commit()
    db.refresh(contact)
    log_action(db, auth_info["user"].id, "Edit", "Contact", contact.id)
    return contact

@router.delete("/{contact_id}")
def delete_contact(
    *,
    db: Session = Depends(deps.get_db),
    contact_id: int,
    auth_info: dict = Depends(deps.PermissionChecker("Contact", "Delete")),
):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
        
    db.delete(contact)
    db.commit()
    log_action(db, auth_info["user"].id, "Delete", "Contact", contact_id)
    return {"message": "Contact deleted successfully"}
