from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Any
from datetime import datetime, timezone, date

from app.api import deps
from app.core.scope import apply_scope
from app.models.domain import GeoTracking, CustomerVisit, Employee
from app.schemas.tracking import (
    GeoTrackingBase, GeoTrackingResponse,
    CustomerVisitCreate, CustomerVisitCheckIn, CustomerVisitCheckOut, CustomerVisitResponse
)
from app.core.audit import log_action
from app.core.pagination import paginate_query

router_tracking = APIRouter()
router_visits = APIRouter()

ALLOWED_GEO_SORT_FIELDS = ["id", "timestamp", "employee_id", "type"]
ALLOWED_VISIT_SORT_FIELDS = ["id", "visit_date", "check_in_time", "check_out_time", "status", "customer_id", "employee_id"]

# --- GEO TRACKING ---

@router_tracking.post("/check-in", response_model=GeoTrackingResponse)
def check_in(
    location_in: GeoTrackingBase,
    request: Request,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Geo", "Geo.CheckIn")),
):
    curr_user = auth_info["user"]
    # Prevent duplicate active check-ins (latest record must not be CheckIn without CheckOut)
    latest = db.query(GeoTracking).filter(GeoTracking.employee_id == curr_user.id).order_by(GeoTracking.timestamp.desc()).first()
    if latest and latest.type == "CheckIn":
        raise HTTPException(status_code=400, detail="Already checked in.")
        
    track = GeoTracking(
        employee_id=curr_user.id,
        type="CheckIn",
        latitude=location_in.latitude,
        longitude=location_in.longitude,
        location_info=location_in.location_info,
        customer_id=location_in.customer_id,
        visit_id=location_in.visit_id
    )
    db.add(track)
    db.flush()
    
    log_action(
        db,
        curr_user.id,
        "CheckIn",
        "Geo",
        track.id,
        new_val={"latitude": track.latitude, "longitude": track.longitude, "customer_id": track.customer_id, "visit_id": track.visit_id},
        request=request
    )
    db.commit()
    db.refresh(track)
    return track

@router_tracking.post("/check-out", response_model=GeoTrackingResponse)
def check_out(
    location_in: GeoTrackingBase,
    request: Request,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Geo", "Geo.CheckOut")),
):
    curr_user = auth_info["user"]
    # Prevent check-out without active check-in
    latest = db.query(GeoTracking).filter(GeoTracking.employee_id == curr_user.id).order_by(GeoTracking.timestamp.desc()).first()
    if not latest or latest.type == "CheckOut":
        raise HTTPException(status_code=400, detail="Cannot check out without an active check-in.")
        
    track = GeoTracking(
        employee_id=curr_user.id,
        type="CheckOut",
        latitude=location_in.latitude,
        longitude=location_in.longitude,
        location_info=location_in.location_info,
        customer_id=location_in.customer_id,
        visit_id=location_in.visit_id
    )
    db.add(track)
    db.flush()
    
    log_action(
        db,
        curr_user.id,
        "CheckOut",
        "Geo",
        track.id,
        new_val={"latitude": track.latitude, "longitude": track.longitude, "customer_id": track.customer_id, "visit_id": track.visit_id},
        request=request
    )
    db.commit()
    db.refresh(track)
    return track

@router_tracking.get("/latest", response_model=List[GeoTrackingResponse])
def get_latest_locations(
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Geo", "Geo.ViewLiveLocation")),
):
    # Strictly ONE latest point per employee
    max_ids_subq = (
        db.query(func.max(GeoTracking.id).label("max_id"))
        .group_by(GeoTracking.employee_id)
        .subquery()
    )
    query = db.query(GeoTracking).join(max_ids_subq, GeoTracking.id == max_ids_subq.c.max_id)
    query = apply_scope(query, GeoTracking, auth_info, db)
    return query.order_by(GeoTracking.timestamp.desc()).all()

@router_tracking.get("/history")
def get_tracking_history(
    db: Session = Depends(deps.get_db),
    employee_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = "timestamp",
    sort_dir: Optional[str] = "desc",
    paginate: bool = True,
    raw: bool = False,
    auth_info: dict = Depends(deps.PermissionChecker("Geo", "Geo.ViewLocationHistory")),
):
    query = apply_scope(db.query(GeoTracking), GeoTracking, auth_info, db)

    if employee_id is not None:
        query = query.filter(GeoTracking.employee_id == employee_id)
    if start_date:
        query = query.filter(GeoTracking.timestamp >= start_date)
    if end_date:
        query = query.filter(GeoTracking.timestamp <= end_date)

    return paginate_query(
        query=query,
        model=GeoTracking,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
        allowed_sort_fields=ALLOWED_GEO_SORT_FIELDS,
        default_sort_field="timestamp",
        default_sort_dir="desc",
        paginate=paginate,
        raw=raw,
    )

# --- CUSTOMER VISITS ---

@router_visits.post("/", response_model=CustomerVisitResponse)
def create_visit(
    visit_in: CustomerVisitCreate,
    request: Request,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Visit", "Create")),
):
    visit = CustomerVisit(**visit_in.model_dump(), employee_id=auth_info["user"].id)
    db.add(visit)
    db.flush()
    
    log_action(
        db,
        auth_info["user"].id,
        "Create",
        "CustomerVisit",
        visit.id,
        new_val={"customer_id": visit.customer_id, "purpose": visit.purpose},
        request=request
    )
    db.commit()
    db.refresh(visit)
    return visit

@router_visits.get("/")
def get_visits(
    db: Session = Depends(deps.get_db),
    customer_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = "visit_date",
    sort_dir: Optional[str] = "desc",
    paginate: bool = True,
    raw: bool = False,
    auth_info: dict = Depends(deps.PermissionChecker("Visit", "View")),
):
    query = apply_scope(db.query(CustomerVisit), CustomerVisit, auth_info, db)

    if customer_id is not None:
        query = query.filter(CustomerVisit.customer_id == customer_id)
    if employee_id is not None:
        query = query.filter(CustomerVisit.employee_id == employee_id)
    if status:
        query = query.filter(CustomerVisit.status == status)
    if start_date:
        query = query.filter(CustomerVisit.visit_date >= start_date)
    if end_date:
        query = query.filter(CustomerVisit.visit_date <= end_date)

    return paginate_query(
        query=query,
        model=CustomerVisit,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
        allowed_sort_fields=ALLOWED_VISIT_SORT_FIELDS,
        default_sort_field="id",
        default_sort_dir="desc",
        paginate=paginate,
        raw=raw,
    )

@router_visits.post("/{visit_id}/check-in", response_model=CustomerVisitResponse)
def visit_check_in(
    visit_id: int,
    loc_in: CustomerVisitCheckIn,
    request: Request,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Visit", "Edit")),
):
    visit = apply_scope(db.query(CustomerVisit).filter(CustomerVisit.id == visit_id), CustomerVisit, auth_info, db).first()
    if not visit:
        raise HTTPException(404, "Visit not found")
    if visit.status != "Scheduled":
        raise HTTPException(400, "Visit is not in Scheduled status.")
    
    old_status = visit.status
    visit.status = "InProgress"
    visit.check_in_time = datetime.now(timezone.utc)
    visit.check_in_latitude = loc_in.latitude
    visit.check_in_longitude = loc_in.longitude
    
    log_action(
        db,
        auth_info["user"].id,
        "CheckIn",
        "CustomerVisit",
        visit.id,
        old_val={"status": old_status},
        new_val={"status": visit.status, "latitude": loc_in.latitude, "longitude": loc_in.longitude},
        request=request
    )
    db.commit()
    db.refresh(visit)
    return visit

@router_visits.post("/{visit_id}/check-out", response_model=CustomerVisitResponse)
def visit_check_out(
    visit_id: int,
    loc_in: CustomerVisitCheckOut,
    request: Request,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Visit", "Edit")),
):
    visit = apply_scope(db.query(CustomerVisit).filter(CustomerVisit.id == visit_id), CustomerVisit, auth_info, db).first()
    if not visit:
        raise HTTPException(404, "Visit not found")
    if visit.status != "InProgress":
        raise HTTPException(400, "Visit must be InProgress to check out.")
    
    old_status = visit.status
    visit.status = "Completed"
    visit.check_out_time = datetime.now(timezone.utc)
    visit.check_out_latitude = loc_in.latitude
    visit.check_out_longitude = loc_in.longitude
    if loc_in.remarks:
        visit.remarks = loc_in.remarks
        
    log_action(
        db,
        auth_info["user"].id,
        "CheckOut",
        "CustomerVisit",
        visit.id,
        old_val={"status": old_status},
        new_val={"status": visit.status, "remarks": visit.remarks},
        request=request
    )
    db.commit()
    db.refresh(visit)
    return visit
