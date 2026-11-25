import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from datetime import datetime, timezone, date

from app.api import deps
from app.core.scope import apply_scope
from app.models.domain import (
    Activity, Task, Meeting, Lead, Opportunity, Customer, Contact, Employee
)
from app.schemas.engagement import (
    ActivityCreate, ActivityUpdate, ActivityResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    MeetingCreate, MeetingUpdate, MeetingResponse
)
from app.core.audit import log_action
from app.core.pagination import paginate_query

router_activities = APIRouter()
router_tasks = APIRouter()
router_meetings = APIRouter()

ALLOWED_ACT_SORT = ["id", "date", "type", "employee_id", "related_to_entity"]
ALLOWED_TASK_SORT = ["id", "title", "due_date", "priority", "status", "assigned_employee_id"]
ALLOWED_MEET_SORT = ["id", "subject", "date", "start_time", "end_time", "status", "employee_id"]

def _validate_relation(db: Session, auth_info: dict, entity: Optional[str], entity_id: Optional[int]):
    if not entity or not entity_id:
        return
    if entity == "Lead":
        lead = apply_scope(db.query(Lead).filter(Lead.id == entity_id), Lead, auth_info, db).first()
        if not lead:
            raise HTTPException(status_code=400, detail="Related Lead not found or outside authorized scope.")
    elif entity == "Opportunity":
        opp = apply_scope(db.query(Opportunity).filter(Opportunity.id == entity_id), Opportunity, auth_info, db).first()
        if not opp:
            raise HTTPException(status_code=400, detail="Related Opportunity not found or outside authorized scope.")
    elif entity == "Customer":
        cust = apply_scope(db.query(Customer).filter(Customer.id == entity_id), Customer, auth_info, db).first()
        if not cust:
            raise HTTPException(status_code=400, detail="Related Customer not found or outside authorized scope.")
    elif entity == "Contact":
        cont = apply_scope(db.query(Contact).filter(Contact.id == entity_id), Contact, auth_info, db).first()
        if not cont:
            raise HTTPException(status_code=400, detail="Related Contact not found or outside authorized scope.")

# --- ACTIVITIES ---

@router_activities.post("/", response_model=ActivityResponse)
def create_activity(
    activity_in: ActivityCreate,
    request: Request,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Activity", "Create"))
):
    _validate_relation(db, auth_info, activity_in.related_to_entity, activity_in.related_to_id)

    db_act = Activity(**activity_in.model_dump())
    if not db_act.employee_id:
        db_act.employee_id = auth_info["user"].id
    if not db_act.date:
        db_act.date = datetime.now(timezone.utc)

    db.add(db_act)
    db.flush()
    
    log_action(
        db,
        auth_info["user"].id,
        "Create",
        "Activity",
        db_act.id,
        new_val={"type": db_act.type, "related_to_entity": db_act.related_to_entity, "related_to_id": db_act.related_to_id},
        request=request
    )
    db.commit()
    db.refresh(db_act)
    return db_act

@router_activities.get("/")
def get_activities(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = "id",
    sort_dir: Optional[str] = "desc",
    paginate: bool = True,
    raw: bool = False,
    auth_info: dict = Depends(deps.PermissionChecker("Activity", "View"))
):
    query = apply_scope(db.query(Activity), Activity, auth_info, db)
    return paginate_query(
        query=query,
        model=Activity,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
        allowed_sort_fields=ALLOWED_ACT_SORT,
        default_sort_field="id",
        default_sort_dir="desc",
        paginate=paginate,
        raw=raw,
    )

@router_activities.put("/{activity_id}", response_model=ActivityResponse)
def update_activity(
    activity_id: int,
    activity_in: ActivityUpdate,
    request: Request,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Activity", "Edit"))
):
    act = apply_scope(db.query(Activity).filter(Activity.id == activity_id), Activity, auth_info, db).first()
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")

    update_data = activity_in.model_dump(exclude_unset=True)
    check_entity = update_data.get("related_to_entity", act.related_to_entity)
    check_id = update_data.get("related_to_id", act.related_to_id)
    _validate_relation(db, auth_info, check_entity, check_id)

    old_vals = {}
    new_vals = {}
    for k, v in update_data.items():
        curr_val = getattr(act, k)
        if curr_val != v:
            old_vals[k] = curr_val
            new_vals[k] = v
            setattr(act, k, v)

    log_action(
        db,
        auth_info["user"].id,
        "Edit",
        "Activity",
        act.id,
        old_val=old_vals,
        new_val=new_vals,
        request=request
    )
    db.commit()
    db.refresh(act)
    return act

@router_activities.delete("/{activity_id}")
def delete_activity(
    activity_id: int,
    request: Request,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Activity", "Delete"))
):
    act = apply_scope(db.query(Activity).filter(Activity.id == activity_id), Activity, auth_info, db).first()
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")

    log_action(
        db,
        auth_info["user"].id,
        "Delete",
        "Activity",
        activity_id,
        old_val={"type": act.type, "description": act.description},
        request=request
    )
    db.delete(act)
    db.commit()
    return {"message": "Activity deleted successfully"}

# --- TASKS ---

@router_tasks.post("/", response_model=TaskResponse)
def create_task(
    task_in: TaskCreate,
    request: Request,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Task", "Create"))
):
    _validate_relation(db, auth_info, task_in.related_to_entity, task_in.related_to_id)

    db_task = Task(**task_in.model_dump())
    if not db_task.assigned_employee_id:
        db_task.assigned_employee_id = auth_info["user"].id

    db.add(db_task)
    db.flush()
    
    log_action(
        db,
        auth_info["user"].id,
        "Create",
        "Task",
        db_task.id,
        new_val={"title": db_task.title, "due_date": str(db_task.due_date), "status": db_task.status},
        request=request
    )
    db.commit()
    db.refresh(db_task)
    return db_task

@router_tasks.get("/")
def get_tasks(
    db: Session = Depends(deps.get_db),
    overdue: bool = False,
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = "due_date",
    sort_dir: Optional[str] = "asc",
    paginate: bool = True,
    raw: bool = False,
    auth_info: dict = Depends(deps.PermissionChecker("Task", "View"))
):
    query = apply_scope(db.query(Task), Task, auth_info, db)
    if overdue:
        query = query.filter(Task.due_date < date.today(), Task.status.notin_(["Completed", "Cancelled"]))

    return paginate_query(
        query=query,
        model=Task,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
        allowed_sort_fields=ALLOWED_TASK_SORT,
        default_sort_field="due_date",
        default_sort_dir="asc",
        paginate=paginate,
        raw=raw,
    )

@router_tasks.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    request: Request,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Task", "Edit"))
):
    task = apply_scope(db.query(Task).filter(Task.id == task_id), Task, auth_info, db).first()
    if not task:
        raise HTTPException(404, "Task not found")
    
    update_data = task_in.model_dump(exclude_unset=True)
    check_entity = update_data.get("related_to_entity", task.related_to_entity)
    check_id = update_data.get("related_to_id", task.related_to_id)
    _validate_relation(db, auth_info, check_entity, check_id)

    if "status" in update_data and update_data["status"] == "Completed" and task.status != "Completed":
        task.completion_date = datetime.now(timezone.utc)
        
    old_vals = {}
    new_vals = {}
    for k, v in update_data.items():
        curr_val = getattr(task, k)
        if curr_val != v:
            old_vals[k] = str(curr_val) if isinstance(curr_val, (date, datetime)) else curr_val
            new_vals[k] = str(v) if isinstance(v, (date, datetime)) else v
            setattr(task, k, v)

    log_action(
        db,
        auth_info["user"].id,
        "Edit",
        "Task",
        task.id,
        old_val=old_vals,
        new_val=new_vals,
        request=request
    )
    db.commit()
    db.refresh(task)
    return task

@router_tasks.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: int,
    request: Request,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Task", "Edit"))
):
    task = apply_scope(db.query(Task).filter(Task.id == task_id), Task, auth_info, db).first()
    if not task:
        raise HTTPException(404, "Task not found")

    old_status = task.status
    task.status = "Completed"
    task.completion_date = datetime.now(timezone.utc)

    log_action(
        db,
        auth_info["user"].id,
        "Complete",
        "Task",
        task.id,
        old_val={"status": old_status},
        new_val={"status": "Completed", "completion_date": task.completion_date.isoformat()},
        request=request
    )
    db.commit()
    db.refresh(task)
    return task

@router_tasks.post("/{task_id}/cancel", response_model=TaskResponse)
def cancel_task(
    task_id: int,
    request: Request,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Task", "Edit"))
):
    task = apply_scope(db.query(Task).filter(Task.id == task_id), Task, auth_info, db).first()
    if not task:
        raise HTTPException(404, "Task not found")

    old_status = task.status
    task.status = "Cancelled"

    log_action(
        db,
        auth_info["user"].id,
        "Cancel",
        "Task",
        task.id,
        old_val={"status": old_status},
        new_val={"status": "Cancelled"},
        request=request
    )
    db.commit()
    db.refresh(task)
    return task

# --- MEETINGS ---

@router_meetings.get("/")
def get_meetings(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = "date",
    sort_dir: Optional[str] = "asc",
    paginate: bool = True,
    raw: bool = False,
    auth_info: dict = Depends(deps.PermissionChecker("Meeting", "View"))
):
    query = apply_scope(db.query(Meeting), Meeting, auth_info, db)
    return paginate_query(
        query=query,
        model=Meeting,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
        allowed_sort_fields=ALLOWED_MEET_SORT,
        default_sort_field="date",
        default_sort_dir="asc",
        paginate=paginate,
        raw=raw,
    )

@router_meetings.post("/", response_model=MeetingResponse)
def create_meeting(
    meeting_in: MeetingCreate,
    request: Request,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Meeting", "Create"))
):
    if meeting_in.start_time >= meeting_in.end_time:
        raise HTTPException(400, "Start time must be before end time.")

    _validate_relation(db, auth_info, meeting_in.related_to_entity, meeting_in.related_to_id)
        
    emp_id = meeting_in.employee_id or auth_info["user"].id
    conflict = db.query(Meeting).filter(
        Meeting.employee_id == emp_id,
        Meeting.date == meeting_in.date,
        Meeting.status != "Cancelled",
        Meeting.start_time < meeting_in.end_time,
        Meeting.end_time > meeting_in.start_time
    ).first()
    if conflict:
        raise HTTPException(400, "Scheduling conflict detected for this employee.")
        
    db_meeting = Meeting(**meeting_in.model_dump())
    if not db_meeting.employee_id:
        db_meeting.employee_id = auth_info["user"].id

    db.add(db_meeting)
    db.flush()
    
    log_action(
        db,
        auth_info["user"].id,
        "Create",
        "Meeting",
        db_meeting.id,
        new_val={"subject": db_meeting.subject, "date": str(db_meeting.date), "status": db_meeting.status},
        request=request
    )
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

@router_meetings.put("/{meeting_id}", response_model=MeetingResponse)
def update_meeting(
    meeting_id: int,
    meeting_in: MeetingUpdate,
    request: Request,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Meeting", "Edit"))
):
    meeting = apply_scope(db.query(Meeting).filter(Meeting.id == meeting_id), Meeting, auth_info, db).first()
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    
    update_data = meeting_in.model_dump(exclude_unset=True)
    check_date = update_data.get("date", meeting.date)
    check_start = update_data.get("start_time", meeting.start_time)
    check_end = update_data.get("end_time", meeting.end_time)
    check_status = update_data.get("status", meeting.status)
    check_emp = update_data.get("employee_id", meeting.employee_id)
    
    if check_start >= check_end:
        raise HTTPException(400, "Start time must be before end time.")
        
    # Check conflict if meeting is Scheduled or Rescheduled
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

    old_vals = {}
    new_vals = {}
    for k, v in update_data.items():
        curr_val = getattr(meeting, k)
        if curr_val != v:
            old_vals[k] = str(curr_val) if isinstance(curr_val, (date, datetime)) else curr_val
            new_vals[k] = str(v) if isinstance(v, (date, datetime)) else v
            setattr(meeting, k, v)

    action_label = "Reschedule" if update_data.get("status") == "Rescheduled" else "Edit"
    log_action(
        db,
        auth_info["user"].id,
        action_label,
        "Meeting",
        meeting.id,
        old_val=old_vals,
        new_val=new_vals,
        request=request
    )
    db.commit()
    db.refresh(meeting)
    return meeting
