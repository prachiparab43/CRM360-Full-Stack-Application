from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LeadBase(BaseModel):
    name: str
    company: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    lead_source: Optional[str] = None
    assigned_employee_id: Optional[int] = None
    requirement: Optional[str] = None
    notes: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    assigned_employee_id: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class LeadQualify(BaseModel):
    expected_value: Optional[float] = 0.0
    probability: Optional[float] = 0.0

class LeadDisqualify(BaseModel):
    reason: str

class LeadResponse(LeadBase):
    id: int
    status: str
    disqualified_reason: Optional[str] = None
    created_date: Optional[datetime]
    class Config:
        from_attributes = True
