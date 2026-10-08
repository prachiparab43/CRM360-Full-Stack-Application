from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, time, datetime

class ActivityBase(BaseModel):
    type: str
    description: Optional[str] = None
    employee_id: Optional[int] = None
    related_to_entity: Optional[str] = None
    related_to_id: Optional[int] = None

class ActivityCreate(ActivityBase):
    pass

class ActivityUpdate(BaseModel):
    type: Optional[str] = None
    description: Optional[str] = None
    employee_id: Optional[int] = None
    related_to_entity: Optional[str] = None
    related_to_id: Optional[int] = None

class ActivityResponse(ActivityBase):
    id: int
    date: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = "Pending"
    priority: Optional[str] = "Medium"
    assigned_employee_id: Optional[int] = None
    related_to_entity: Optional[str] = None
    related_to_id: Optional[int] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_employee_id: Optional[int] = None
    related_to_entity: Optional[str] = None
    related_to_id: Optional[int] = None

class TaskResponse(TaskBase):
    id: int
    completion_date: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class MeetingBase(BaseModel):
    subject: str
    date: date
    start_time: time
    end_time: time
    location: Optional[str] = None
    participants: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = "Scheduled"
    employee_id: Optional[int] = None
    related_to_entity: Optional[str] = None
    related_to_id: Optional[int] = None

class MeetingCreate(MeetingBase):
    pass

class MeetingUpdate(BaseModel):
    subject: Optional[str] = None
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = None
    status: Optional[str] = None

class MeetingResponse(MeetingBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
