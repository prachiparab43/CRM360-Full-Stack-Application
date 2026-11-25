from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime

class OpportunityBase(BaseModel):
    name: str
    lead_id: Optional[int] = None
    customer_id: Optional[int] = None
    expected_value: Optional[float] = Field(None, ge=0, description="Expected monetary value must be >= 0")
    probability: Optional[float] = Field(None, ge=0, le=100, description="Probability must be between 0 and 100")
    expected_close_date: Optional[date] = None
    assigned_employee_id: Optional[int] = None
    description: Optional[str] = None
    notes: Optional[str] = None

class OpportunityCreate(OpportunityBase):
    stage: Optional[str] = "Opportunity"

    @field_validator("expected_close_date")
    @classmethod
    def validate_close_date_not_past(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v < date.today():
            raise ValueError("Expected close date cannot be before creation date.")
        return v

class OpportunityUpdate(BaseModel):
    name: Optional[str] = None
    expected_value: Optional[float] = Field(None, ge=0)
    probability: Optional[float] = Field(None, ge=0, le=100)
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
    created_date: Optional[datetime] = None
    lead_name: Optional[str] = None
    lead_company: Optional[str] = None
    lead_contact_name: Optional[str] = None
    lead_email: Optional[str] = None
    lead_phone: Optional[str] = None
    lead_source: Optional[str] = None
    lead_created_date: Optional[datetime] = None
    customer_name: Optional[str] = None
    assigned_employee_name: Optional[str] = None

    class Config:
        from_attributes = True
