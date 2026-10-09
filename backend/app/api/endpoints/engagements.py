from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.api import deps
from app.api.endpoints.dashboard import apply_scope
from app.models.domain import Activity, Task, Meeting
from app.schemas.engagement import (
    ActivityCreate, ActivityUpdate, ActivityResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    MeetingCreate, MeetingUpdate, MeetingResponse
)
from app.core.audit import log_action

router_activities = APIRouter()
router_tasks = APIRouter()
router_meetings = APIRouter()

# --- ACTIVITIES ---
@router_activities.post("/", response_model=ActivityResponse)
def create_activity(activity_in: ActivityCreate, db: Session = Depends(deps.get_db), auth_info: dict = Depends(deps.PermissionChecker("Activity", "Create"))):
    db_act = Activity(**activity_in.model_dump())
    db.add(db_act)
    db.commit()
    db.refresh(db_act)
    log_action(db, auth_info["user"].id, "Create", "Activity", db_act.id)
    return db_act

@router_activities.get("/", response_model=List[ActivityResponse])
def get_activities(db: Session = Depends(deps.get_db), auth_info: dict = Depends(deps.PermissionChecker("Activity", "View"))):
    return db.query(Activity).order_by(Activity.id.desc()).all()

# --- TASKS ---
@router_tasks.post("/", response_model=TaskResponse)
def create_task(task_in: TaskCreate, db: Session = Depends(deps.get_db), auth_info: dict = Depends(deps.PermissionChecker("Task", "Create"))):
    db_task = Task(**task_in.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    log_action(db, auth_info["user"].id, "Create", "Task", db_task.id)
    return db_task

@router_tasks.get("/", response_model=List[TaskResponse])
def get_tasks(
    db: Session = Depends(deps.get_db),
    overdue: bool = False,
    auth_info: dict = Depends(deps.PermissionChecker("Task", "View"))
):
    query = db.query(Task)
    if auth_info["scope"] == "Own":
        query = query.filter(Task.assigned_employee_id == auth_info["user"].id)
    if overdue:
        query = query.filter(Task.due_date < datetime.now().date(), Task.status.notin_(["Completed", "Cancelled"]))
    return query.order_by(Task.due_date).all()

@router_tasks.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_in: TaskUpdate, db: Session = Depends(deps.get_db), auth_info: dict = Depends(deps.PermissionChecker("Task", "Edit"))):
    task = apply_scope(db.query(Task).filter(Task.id == task_id), Task, auth_info).first()
    if not task: raise HTTPException(404, "Task not found")
    
    update_data = task_in.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] == "Completed" and task.status != "Completed":
        task.completion_date = datetime.utcnow()
        
    for k, v in update_data.items(): setattr(task, k, v)
    db.commit()
    db.refresh(task)
    log_action(db, auth_info["user"].id, "Edit", "Task", task.id)
    return task

# --- MEETINGS ---
@router_meetings.get("/", response_model=List[MeetingResponse])
def get_meetings(
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Meeting", "View"))
):
    from app.api.endpoints.dashboard import apply_scope
    query = apply_scope(db.query(Meeting), Meeting, auth_info)
    return query.all()

@router_meetings.post("/", response_model=MeetingResponse)
def create_meeting(meeting_in: MeetingCreate, db: Session = Depends(deps.get_db), auth_info: dict = Depends(deps.PermissionChecker("Meeting", "Create"))):
    if meeting_in.start_time >= meeting_in.end_time:
        raise HTTPException(400, "Start time must be before end time.")
        
    # Check conflicts
    conflict = db.query(Meeting).filter(
        Meeting.employee_id == meeting_in.employee_id,
        Meeting.date == meeting_in.date,
        Meeting.status != "Cancelled",
        Meeting.start_time < meeting_in.end_time,
        Meeting.end_time > meeting_in.start_time
    ).first()
    if conflict:
        raise HTTPException(400, "Scheduling conflict detected for this employee.")
        
    db_meeting = Meeting(**meeting_in.model_dump())
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    log_action(db, auth_info["user"].id, "Create", "Meeting", db_meeting.id)
    return db_meeting

@router_meetings.put("/{meeting_id}", response_model=MeetingResponse)
def update_meeting(meeting_id: int, meeting_in: MeetingUpdate, db: Session = Depends(deps.get_db), auth_info: dict = Depends(deps.PermissionChecker("Meeting", "Edit"))):
    meeting = apply_scope(db.query(Meeting).filter(Meeting.id == meeting_id), Meeting, auth_info).first()
    if not meeting: raise HTTPException(404, "Meeting not found")
    
    update_data = meeting_in.model_dump(exclude_unset=True)
    
    # Validation if times/date are updated
    check_date = update_data.get("date", meeting.date)
    check_start = update_data.get("start_time", meeting.start_time)
    check_end = update_data.get("end_time", meeting.end_time)
    check_status = update_data.get("status", meeting.status)
    check_emp = update_data.get("employee_id", meeting.employee_id)
    
    if check_start >= check_end:
        raise HTTPException(400, "Start time must be before end time.")
        
    if check_status != "Cancelled":
        conflict = db.query(Meeting).filter(
            Meeting.id != meeting.id,
            Meeting.employee_id == check_emp,
            Meeting.date == check_date,
            Meeting.status != "Cancelled",
            Meeting.start_time < check_end,
            Meeting.end_time > check_start
        ).first()
        if conflict:
            raise HTTPException(400, "Scheduling conflict detected for this employee.")

    for k, v in update_data.items(): setattr(meeting, k, v)
    db.commit()
    db.refresh(meeting)
    log_action(db, auth_info["user"].id, "Edit", "Meeting", meeting.id)
    return meeting
