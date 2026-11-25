import csv
import io
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.api import deps
from app.models.domain import (
    Lead, Opportunity, Customer, Employee, Activity, Task, Meeting, CustomerVisit, GeoTracking
)
from app.core.scope import apply_scope
from app.core.audit import log_action

router = APIRouter()

def generate_csv_response(filename: str, headers: list, rows: list):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    
    output.seek(0)
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response

# --- 1. LEAD REPORT ---

@router.get("/leads")
def report_leads(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None,
    lead_source: Optional[str] = None,
    employee_id: Optional[int] = None,
    format: str = Query("json"),
    request: Request = None,
    auth_info: dict = Depends(deps.PermissionChecker("Report", "View")),
):
    is_csv = format.lower() == "csv"
    if is_csv:
        deps.PermissionChecker("Report", "Export")(auth_info["user"], db)

    query = apply_scope(db.query(Lead), Lead, auth_info, db)
    if start_date:
        query = query.filter(func.cast(Lead.created_date, date) >= start_date)
    if end_date:
        query = query.filter(func.cast(Lead.created_date, date) <= end_date)
    if status:
        query = query.filter(Lead.status == status)
    if lead_source:
        query = query.filter(Lead.lead_source == lead_source)
    if employee_id is not None:
        query = query.filter(Lead.assigned_employee_id == employee_id)

    leads = query.all()

    if is_csv:
        headers = ["ID", "Name", "Company", "Status", "Source", "Assigned Employee ID", "Created Date"]
        rows = [
            [
                l.id, l.name, l.company, l.status, l.lead_source, l.assigned_employee_id,
                l.created_date.isoformat() if l.created_date else ""
            ]
            for l in leads
        ]
        log_action(db, auth_info["user"].id, "Export", "Report", 0, new_val="leads_report.csv", request=request)
        db.commit()
        return generate_csv_response("leads_report.csv", headers, rows)

    # Breakdown aggregations
    by_status = {}
    by_source = {}
    by_employee = {}
    converted_count = 0

    for l in leads:
        st = l.status or "Unknown"
        by_status[st] = by_status.get(st, 0) + 1

        src = l.lead_source or "Unspecified"
        by_source[src] = by_source.get(src, 0) + 1

        emp = l.assigned_employee.name if l.assigned_employee else "Unassigned"
        by_employee[emp] = by_employee.get(emp, 0) + 1

        if l.status == "Qualified" or l.opportunity is not None:
            converted_count += 1

    total = len(leads)
    conversion_rate = round((converted_count / total * 100), 2) if total > 0 else 0.0

    log_action(db, auth_info["user"].id, "View", "Report", 0, new_val="leads_summary", request=request)
    db.commit()

    return {
        "total_leads": total,
        "converted_to_opportunity": converted_count,
        "conversion_rate_percent": conversion_rate,
        "by_status": by_status,
        "by_source": by_source,
        "by_employee": by_employee,
    }

@router.get("/leads/export")
def export_leads_csv(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None,
    lead_source: Optional[str] = None,
    employee_id: Optional[int] = None,
    request: Request = None,
    auth_info: dict = Depends(deps.PermissionChecker("Report", "Export")),
):
    return report_leads(
        db=db,
        start_date=start_date,
        end_date=end_date,
        status=status,
        lead_source=lead_source,
        employee_id=employee_id,
        format="csv",
        request=request,
        auth_info=auth_info,
    )

# --- 2. OPPORTUNITY REPORT ---

@router.get("/opportunities")
def report_opportunities(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    stage: Optional[str] = None,
    employee_id: Optional[int] = None,
    format: str = Query("json"),
    request: Request = None,
    auth_info: dict = Depends(deps.PermissionChecker("Report", "View")),
):
    is_csv = format.lower() == "csv"
    if is_csv:
        deps.PermissionChecker("Report", "Export")(auth_info["user"], db)

    query = apply_scope(db.query(Opportunity), Opportunity, auth_info, db)
    if start_date:
        query = query.filter(Opportunity.expected_close_date >= start_date)
    if end_date:
        query = query.filter(Opportunity.expected_close_date <= end_date)
    if stage:
        query = query.filter(Opportunity.stage == stage)
    if employee_id is not None:
        query = query.filter(Opportunity.assigned_employee_id == employee_id)

    opps = query.all()

    if is_csv:
        headers = ["ID", "Name", "Expected Value", "Stage", "Assigned Employee ID"]
        rows = [
            [o.id, o.name, o.expected_value, o.stage, o.assigned_employee_id]
            for o in opps
        ]
        log_action(db, auth_info["user"].id, "Export", "Report", 0, new_val="opportunities_export.csv", request=request)
        db.commit()
        return generate_csv_response("opportunities_export.csv", headers, rows)

    by_stage = {}
    by_employee = {}
    lost_reasons = {}
    total_expected_revenue = 0.0
    total_won_revenue = 0.0
    won_count = 0
    lost_count = 0

    for o in opps:
        st = o.stage or "Opportunity"
        by_stage[st] = by_stage.get(st, 0) + 1

        val = float(o.expected_value or 0.0)
        total_expected_revenue += val

        if st == "Won":
            won_count += 1
            total_won_revenue += val
        elif st == "Lost":
            lost_count += 1
            r = (o.lost_reason or "Unknown").strip()
            lost_reasons[r] = lost_reasons.get(r, 0) + 1

        emp = o.assigned_employee.name if o.assigned_employee else "Unassigned"
        by_employee[emp] = by_employee.get(emp, 0) + val

    log_action(db, auth_info["user"].id, "View", "Report", 0, new_val="opportunities_summary", request=request)
    db.commit()

    return {
        "total_opportunities": len(opps),
        "won_count": won_count,
        "lost_count": lost_count,
        "total_expected_revenue": round(total_expected_revenue, 2),
        "total_won_revenue": round(total_won_revenue, 2),
        "by_stage": by_stage,
        "by_employee_revenue": by_employee,
        "lost_reasons": lost_reasons,
    }

@router.get("/opportunities/export")
def export_opportunities(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    stage: Optional[str] = None,
    employee_id: Optional[int] = None,
    request: Request = None,
    auth_info: dict = Depends(deps.PermissionChecker("Report", "Export"))
):
    return report_opportunities(
        db=db,
        start_date=start_date,
        end_date=end_date,
        stage=stage,
        employee_id=employee_id,
        format="csv",
        request=request,
        auth_info=auth_info
    )

# --- 3. CUSTOMER REPORT ---

@router.get("/customers")
def report_customers(
    db: Session = Depends(deps.get_db),
    industry: Optional[str] = None,
    status: Optional[str] = None,
    employee_id: Optional[int] = None,
    format: str = Query("json"),
    request: Request = None,
    auth_info: dict = Depends(deps.PermissionChecker("Report", "View")),
):
    is_csv = format.lower() == "csv"
    if is_csv:
        deps.PermissionChecker("Report", "Export")(auth_info["user"], db)

    query = apply_scope(db.query(Customer), Customer, auth_info, db)
    if industry:
        query = query.filter(Customer.industry == industry)
    if status:
        query = query.filter(Customer.status == status)
    if employee_id is not None:
        query = query.filter(Customer.assigned_employee_id == employee_id)

    customers = query.all()

    if is_csv:
        headers = ["ID", "Name", "Industry", "Status", "Email", "Phone", "Assigned Employee ID"]
        rows = [[c.id, c.name, c.industry or "", c.status, c.email or "", c.phone or "", c.assigned_employee_id] for c in customers]
        log_action(db, auth_info["user"].id, "Export", "Report", 0, new_val="customers_report.csv", request=request)
        db.commit()
        return generate_csv_response("customers_report.csv", headers, rows)

    by_industry = {}
    by_status = {}
    by_employee = {}

    for c in customers:
        ind = c.industry or "Unspecified"
        by_industry[ind] = by_industry.get(ind, 0) + 1

        st = c.status or "Active"
        by_status[st] = by_status.get(st, 0) + 1

        emp = c.assigned_employee.name if c.assigned_employee else "Unassigned"
        by_employee[emp] = by_employee.get(emp, 0) + 1

    log_action(db, auth_info["user"].id, "View", "Report", 0, new_val="customers_summary", request=request)
    db.commit()

    return {
        "total_customers": len(customers),
        "by_industry": by_industry,
        "by_status": by_status,
        "by_employee": by_employee,
    }

@router.get("/customers/export")
def export_customers_csv(
    db: Session = Depends(deps.get_db),
    industry: Optional[str] = None,
    status: Optional[str] = None,
    employee_id: Optional[int] = None,
    request: Request = None,
    auth_info: dict = Depends(deps.PermissionChecker("Report", "Export")),
):
    return report_customers(
        db=db,
        industry=industry,
        status=status,
        employee_id=employee_id,
        format="csv",
        request=request,
        auth_info=auth_info,
    )

# --- 4. EMPLOYEE ACTIVITY REPORT ---

@router.get("/employees")
def report_employees(
    db: Session = Depends(deps.get_db),
    employee_id: Optional[int] = None,
    format: str = Query("json"),
    request: Request = None,
    auth_info: dict = Depends(deps.PermissionChecker("Report", "View")),
):
    is_csv = format.lower() == "csv"
    if is_csv:
        deps.PermissionChecker("Report", "Export")(auth_info["user"], db)

    query = apply_scope(db.query(Employee), Employee, auth_info, db)
    if employee_id is not None:
        query = query.filter(Employee.id == employee_id)

    employees = query.all()
    emp_ids = [e.id for e in employees]

    # Batch counts
    act_counts = dict(db.query(Activity.employee_id, func.count(Activity.id)).filter(Activity.employee_id.in_(emp_ids)).group_by(Activity.employee_id).all())
    task_counts = dict(db.query(Task.assigned_employee_id, func.count(Task.id)).filter(Task.assigned_employee_id.in_(emp_ids)).group_by(Task.assigned_employee_id).all())
    meet_counts = dict(db.query(Meeting.employee_id, func.count(Meeting.id)).filter(Meeting.employee_id.in_(emp_ids)).group_by(Meeting.employee_id).all())
    visit_counts = dict(db.query(CustomerVisit.employee_id, func.count(CustomerVisit.id)).filter(CustomerVisit.employee_id.in_(emp_ids)).group_by(CustomerVisit.employee_id).all())

    if is_csv:
        headers = ["Employee ID", "Name", "Department", "Designation", "Activities", "Tasks", "Meetings", "Visits"]
        rows = [
            [
                e.id, e.name, e.department or "", e.designation or "",
                act_counts.get(e.id, 0), task_counts.get(e.id, 0), meet_counts.get(e.id, 0), visit_counts.get(e.id, 0)
            ]
            for e in employees
        ]
        log_action(db, auth_info["user"].id, "Export", "Report", 0, new_val="employees_report.csv", request=request)
        db.commit()
        return generate_csv_response("employees_report.csv", headers, rows)

    summary = [
        {
            "employee_id": e.id,
            "name": e.name,
            "department": e.department,
            "designation": e.designation,
            "activities_count": act_counts.get(e.id, 0),
            "tasks_count": task_counts.get(e.id, 0),
            "meetings_count": meet_counts.get(e.id, 0),
            "visits_count": visit_counts.get(e.id, 0),
        }
        for e in employees
    ]

    log_action(db, auth_info["user"].id, "View", "Report", 0, new_val="employees_summary", request=request)
    db.commit()
    return {"employees": summary, "total_employees": len(employees)}

@router.get("/employees/export")
def export_employees_csv(
    db: Session = Depends(deps.get_db),
    employee_id: Optional[int] = None,
    request: Request = None,
    auth_info: dict = Depends(deps.PermissionChecker("Report", "Export")),
):
    return report_employees(
        db=db,
        employee_id=employee_id,
        format="csv",
        request=request,
        auth_info=auth_info,
    )

# --- 5. GEO & VISITS REPORT ---

@router.get("/geo")
def report_geo(
    db: Session = Depends(deps.get_db),
    employee_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format: str = Query("json"),
    request: Request = None,
    auth_info: dict = Depends(deps.PermissionChecker("Report", "View")),
):
    is_csv = format.lower() == "csv"
    if is_csv:
        deps.PermissionChecker("Report", "Export")(auth_info["user"], db)

    geo_q = apply_scope(db.query(GeoTracking), GeoTracking, auth_info, db)
    visit_q = apply_scope(db.query(CustomerVisit), CustomerVisit, auth_info, db)

    if employee_id is not None:
        geo_q = geo_q.filter(GeoTracking.employee_id == employee_id)
        visit_q = visit_q.filter(CustomerVisit.employee_id == employee_id)
    if start_date:
        geo_q = geo_q.filter(func.cast(GeoTracking.timestamp, date) >= start_date)
        visit_q = visit_q.filter(CustomerVisit.visit_date >= start_date)
    if end_date:
        geo_q = geo_q.filter(func.cast(GeoTracking.timestamp, date) <= end_date)
        visit_q = visit_q.filter(CustomerVisit.visit_date <= end_date)

    geo_logs = geo_q.order_by(GeoTracking.timestamp.desc()).all()
    visits = visit_q.order_by(CustomerVisit.id.desc()).all()

    if is_csv:
        headers = ["Type", "Record ID", "Employee ID", "Date/Time", "Latitude", "Longitude", "Info/Status"]
        rows = [
            ["GeoTracking", g.id, g.employee_id, g.timestamp.isoformat() if g.timestamp else "", g.latitude, g.longitude, g.type]
            for g in geo_logs
        ] + [
            ["Visit", v.id, v.employee_id, v.visit_date.isoformat() if v.visit_date else "", v.check_in_latitude or "", v.check_in_longitude or "", v.status]
            for v in visits
        ]
        log_action(db, auth_info["user"].id, "Export", "Report", 0, new_val="geo_report.csv", request=request)
        db.commit()
        return generate_csv_response("geo_report.csv", headers, rows)

    log_action(db, auth_info["user"].id, "View", "Report", 0, new_val="geo_summary", request=request)
    db.commit()

    return {
        "total_geo_points": len(geo_logs),
        "total_visits": len(visits),
        "check_ins_count": sum(1 for g in geo_logs if g.type == "CheckIn"),
        "check_outs_count": sum(1 for g in geo_logs if g.type == "CheckOut"),
        "completed_visits": sum(1 for v in visits if v.status == "Completed"),
    }

@router.get("/geo/export")
def export_geo_csv(
    db: Session = Depends(deps.get_db),
    employee_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    request: Request = None,
    auth_info: dict = Depends(deps.PermissionChecker("Report", "Export")),
):
    return report_geo(
        db=db,
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        format="csv",
        request=request,
        auth_info=auth_info,
    )
