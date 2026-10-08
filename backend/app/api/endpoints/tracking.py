from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.api import deps
from app.models.domain import GeoTracking, CustomerVisit, Employee
from app.schemas.tracking import (
    GeoTrackingBase, GeoTrackingResponse,
    CustomerVisitCreate, CustomerVisitCheckIn, CustomerVisitCheckOut, CustomerVisitResponse
)
from app.core.audit import log_action

router_tracking = APIRouter()
router_visits = APIRouter()

# --- GEO TRACKING ---

@router_tracking.post("/check-in", response_model=GeoTrackingResponse)
def check_in(
    location_in: GeoTrackingBase,
    db: Session = Depends(deps.get_db),
    curr_user: Employee = Depends(deps.get_current_active_user)
):
    # Prevent duplicate active check-ins (latest record must not be CheckIn without CheckOut)
    latest = db.query(GeoTracking).filter(GeoTracking.employee_id == curr_user.id).order_by(GeoTracking.timestamp.desc()).first()
    if latest and latest.type == "CheckIn":
        raise HTTPException(status_code=400, detail="Already checked in.")
        
    track = GeoTracking(
        employee_id=curr_user.id,
        type="CheckIn",
        latitude=location_in.latitude,
        longitude=location_in.longitude,
        location_info=location_in.location_info
    )
    db.add(track)
    db.commit()
    db.refresh(track)
    return track

@router_tracking.post("/check-out", response_model=GeoTrackingResponse)
def check_out(
    location_in: GeoTrackingBase,
    db: Session = Depends(deps.get_db),
    curr_user: Employee = Depends(deps.get_current_active_user)
):
    # Prevent check-out without active check-in
    latest = db.query(GeoTracking).filter(GeoTracking.employee_id == curr_user.id).order_by(GeoTracking.timestamp.desc()).first()
    if not latest or latest.type == "CheckOut":
        raise HTTPException(status_code=400, detail="Cannot check out without an active check-in.")
        
    track = GeoTracking(
        employee_id=curr_user.id,
        type="CheckOut",
        latitude=location_in.latitude,
        longitude=location_in.longitude,
        location_info=location_in.location_info
    )
    db.add(track)
    db.commit()
    db.refresh(track)
    return track

@router_tracking.get("/latest", response_model=List[GeoTrackingResponse])
def get_latest_locations(
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("GeoTracking", "View"))
):
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    
    # Subquery to get latest timestamp per employee could be used, or just filter all for simplicity in demo
    # For robust production, use window functions or joined subquery.
    query = db.query(GeoTracking)
    
    if scope == "Own":
        query = query.filter(GeoTracking.employee_id == curr_user.id)
    elif scope in ["Team", "Company"]:
        query = query.join(Employee, GeoTracking.employee_id == Employee.id).filter(Employee.company_id == curr_user.company_id)
        
    return query.order_by(GeoTracking.timestamp.desc()).limit(100).all()

# --- CUSTOMER VISITS ---

@router_visits.post("/", response_model=CustomerVisitResponse)
def create_visit(
    visit_in: CustomerVisitCreate,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Visit", "Create"))
):
    visit = CustomerVisit(**visit_in.model_dump(), employee_id=auth_info["user"].id)
    db.add(visit)
    db.commit()
    db.refresh(visit)
    log_action(db, auth_info["user"].id, "Create", "CustomerVisit", visit.id)
    return visit

@router_visits.get("/", response_model=List[CustomerVisitResponse])
def get_visits(
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Visit", "View"))
):
    query = db.query(CustomerVisit)
    if auth_info["scope"] == "Own":
        query = query.filter(CustomerVisit.employee_id == auth_info["user"].id)
    return query.order_by(CustomerVisit.id.desc()).all()

@router_visits.post("/{visit_id}/check-in", response_model=CustomerVisitResponse)
def visit_check_in(
    visit_id: int,
    loc_in: CustomerVisitCheckIn,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Visit", "Edit"))
):
    visit = db.query(CustomerVisit).filter(CustomerVisit.id == visit_id).first()
    if not visit: raise HTTPException(404, "Visit not found")
    if visit.status != "Scheduled": raise HTTPException(400, "Visit is not in Scheduled status.")
    
    visit.status = "InProgress"
    visit.check_in_time = datetime.utcnow()
    visit.check_in_latitude = loc_in.latitude
    visit.check_in_longitude = loc_in.longitude
    db.commit()
    db.refresh(visit)
    log_action(db, auth_info["user"].id, "CheckIn", "CustomerVisit", visit.id)
    return visit

@router_visits.post("/{visit_id}/check-out", response_model=CustomerVisitResponse)
def visit_check_out(
    visit_id: int,
    loc_in: CustomerVisitCheckOut,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Visit", "Edit"))
):
    visit = db.query(CustomerVisit).filter(CustomerVisit.id == visit_id).first()
    if not visit: raise HTTPException(404, "Visit not found")
    if visit.status != "InProgress": raise HTTPException(400, "Visit must be InProgress to check out.")
    
    visit.status = "Completed"
    visit.check_out_time = datetime.utcnow()
    visit.check_out_latitude = loc_in.latitude
    visit.check_out_longitude = loc_in.longitude
    if loc_in.remarks: visit.remarks = loc_in.remarks
    db.commit()
    db.refresh(visit)
    log_action(db, auth_info["user"].id, "CheckOut", "CustomerVisit", visit.id)
    return visit
