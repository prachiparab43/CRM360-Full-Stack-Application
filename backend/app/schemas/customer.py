from pydantic import BaseModel, EmailStr
from typing import Optional

class CustomerBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    industry: Optional[str] = None
    assigned_employee_id: Optional[int] = None
    status: Optional[str] = "Active"

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    industry: Optional[str] = None
    assigned_employee_id: Optional[int] = None
    status: Optional[str] = None

class CustomerResponse(CustomerBase):
    id: int
    class Config:
        from_attributes = True

class ContactBase(BaseModel):
    name: str
    customer_id: Optional[int] = None
    designation: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    status: Optional[str] = "Active"
    notes: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    name: Optional[str] = None
    customer_id: Optional[int] = None
    designation: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class ContactResponse(ContactBase):
    id: int
    class Config:
        from_attributes = True
