from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from typing import Any

class Token(BaseModel):
    access_token: str
    token_type: str
    status: Optional[str] = "Active"
    user: Optional[dict] = None

class TokenPayload(BaseModel):
    sub: Optional[int] = None

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirm_password: Optional[str] = None
    phone: Optional[str] = None

class RegisterResponse(BaseModel):
    message: str
    status: str
    user: dict

class EmployeeBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    role_id: Optional[int] = None
    company_id: Optional[int] = None
    manager_id: Optional[int] = None
    status: Optional[str] = "Active"
    joining_date: Optional[date] = None

class EmployeeCreate(EmployeeBase):
    password: str
    confirm_password: Optional[str] = None

class PasswordResetRequest(BaseModel):
    password: str
    confirm_password: Optional[str] = None

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    role_id: Optional[int] = None
    company_id: Optional[int] = None
    manager_id: Optional[int] = None
    status: Optional[str] = None
    password: Optional[str] = None

class EmployeeResponse(EmployeeBase):
    id: int
    role_name: Optional[str] = None
    company_name: Optional[str] = None
    
    class Config:
        from_attributes = True
