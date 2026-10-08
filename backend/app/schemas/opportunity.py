from pydantic import BaseModel
from typing import Optional
from datetime import date

class OpportunityBase(BaseModel):
    name: str
    lead_id: Optional[int] = None
    customer_id: Optional[int] = None
    expected_value: Optional[float] = None
    probability: Optional[float] = None
    expected_close_date: Optional[date] = None
    assigned_employee_id: Optional[int] = None
    description: Optional[str] = None
    notes: Optional[str] = None

class OpportunityCreate(OpportunityBase):
    stage: Optional[str] = "Opportunity"

class OpportunityUpdate(BaseModel):
    name: Optional[str] = None
    expected_value: Optional[float] = None
    probability: Optional[float] = None
    expected_close_date: Optional[date] = None
    assigned_employee_id: Optional[int] = None
    description: Optional[str] = None
    notes: Optional[str] = None

class OpportunityStageUpdate(BaseModel):
    stage: str
    lost_reason: Optional[str] = None

class OpportunityResponse(OpportunityBase):
    id: int
    stage: str
    lost_reason: Optional[str] = None
    class Config:
        from_attributes = True
