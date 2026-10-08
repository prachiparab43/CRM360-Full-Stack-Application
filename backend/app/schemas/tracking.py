from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional
from datetime import date, datetime

class CoordinateBase(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class GeoTrackingBase(CoordinateBase):
    location_info: Optional[str] = None

class GeoTrackingCreate(GeoTrackingBase):
    type: str  # CheckIn, CheckOut, Live

class GeoTrackingResponse(GeoTrackingBase):
    id: int
    employee_id: int
    type: str
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class CustomerVisitBase(BaseModel):
    customer_id: int
    contact_id: Optional[int] = None
    visit_date: Optional[date] = None
    location: Optional[str] = None
    purpose: Optional[str] = None
    remarks: Optional[str] = None
    status: Optional[str] = "Scheduled"

class CustomerVisitCreate(CustomerVisitBase):
    pass

class CustomerVisitCheckIn(CoordinateBase):
    pass

class CustomerVisitCheckOut(CoordinateBase):
    remarks: Optional[str] = None

class CustomerVisitResponse(CustomerVisitBase):
    id: int
    employee_id: int
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    check_in_latitude: Optional[float] = None
    check_in_longitude: Optional[float] = None
    check_out_latitude: Optional[float] = None
    check_out_longitude: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)
