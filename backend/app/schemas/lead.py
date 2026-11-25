from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

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

class LeadConvert(BaseModel):
    name: str
    expected_value: Optional[float] = Field(0.0, ge=0)
    probability: Optional[float] = Field(10.0, ge=0, le=100)
    expected_close_date: Optional[date] = None
    stage: Optional[str] = "Opportunity"
    description: Optional[str] = None
    notes: Optional[str] = None
    assigned_employee_id: Optional[int] = None
    customer_id: Optional[int] = None

class LeadResponse(LeadBase):
    id: int
    status: str
    disqualified_reason: Optional[str] = None
    created_date: Optional[datetime] = None
    warning: Optional[str] = None
    opportunity_id: Optional[int] = None
    opportunity_name: Optional[str] = None
    converted_date: Optional[datetime] = None
    assigned_employee_name: Optional[str] = None

    class Config:
        from_attributes = True
