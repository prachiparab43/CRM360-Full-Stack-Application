from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, date

from app.api import deps
from app.models.domain import (
    Lead, Opportunity, Customer, Employee, Task, Meeting, CustomerVisit, GeoTracking, Activity
)
from app.schemas.dashboard import DashboardSummary, DashboardCharts, ChartDataPoint
from app.core.scope import apply_scope, get_team_employee_ids

router = APIRouter()

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Dashboard", "View"))
):
    today = date.today()

    # 1. Lead conditional aggregation (single query)
    leads_q = apply_scope(db.query(Lead), Lead, auth_info, db)
    lead_stats = leads_q.with_entities(
        func.count(Lead.id).label("total"),
        func.sum(case((Lead.status == "New", 1), else_=0)).label("new_leads"),
        func.sum(case((Lead.status == "Contacted", 1), else_=0)).label("contacted_leads"),
        func.sum(case((Lead.status == "Qualified", 1), else_=0)).label("qualified_leads"),
        func.sum(case((Lead.status == "Disqualified", 1), else_=0)).label("disqualified_leads"),
    ).first()

    # 2. Customer conditional aggregation (single query)
    cust_q = apply_scope(db.query(Customer), Customer, auth_info, db)
    cust_stats = cust_q.with_entities(
        func.count(Customer.id).label("total"),
        func.sum(case((Customer.status == "New", 1), else_=0)).label("new_customers"),
        func.sum(case((Customer.status == "Active", 1), else_=0)).label("active_customers"),
    ).first()

    # 3. Opportunity conditional aggregation (single query)
    opp_q = apply_scope(db.query(Opportunity), Opportunity, auth_info, db)
    opp_stats = opp_q.with_entities(
        func.count(Opportunity.id).label("total"),
        func.sum(case((Opportunity.stage == "Won", 1), else_=0)).label("won_opps"),
        func.sum(case((Opportunity.stage == "Lost", 1), else_=0)).label("lost_opps"),
        func.sum(Opportunity.expected_value).label("total_expected_revenue"),
        func.sum(case((Opportunity.stage == "Won", Opportunity.expected_value), else_=0)).label("total_won_revenue"),
        func.sum(case((Opportunity.stage.notin_(["Won", "Lost"]), Opportunity.expected_value), else_=0)).label("pipeline_value"),
    ).first()

    opp_stage_rows = opp_q.with_entities(Opportunity.stage, func.count(Opportunity.id)).group_by(Opportunity.stage).all()
    opportunities_by_stage = {r[0]: int(r[1]) for r in opp_stage_rows if r[0]}

    # 4. Employee conditional aggregation (single query)
    emp_q = apply_scope(db.query(Employee), Employee, auth_info, db)
    emp_stats = emp_q.with_entities(
        func.count(Employee.id).label("total"),
        func.sum(case((Employee.status == "Active", 1), else_=0)).label("active_employees"),
        func.sum(case((Employee.status != "Active", 1), else_=0)).label("inactive_employees"),
    ).first()

    # 5. Task conditional aggregation (single query)
    task_q = apply_scope(db.query(Task), Task, auth_info, db)
    task_stats = task_q.with_entities(
        func.count(Task.id).label("total"),
        func.sum(case((Task.status == "Pending", 1), else_=0)).label("pending_tasks"),
        func.sum(case((Task.status == "Completed", 1), else_=0)).label("completed_tasks"),
        func.sum(case(((Task.due_date < today) & (Task.status.notin_(["Completed", "Cancelled"])), 1), else_=0)).label("overdue_tasks"),
    ).first()

    # 6. CustomerVisit conditional aggregation (single query)
    visit_q = apply_scope(db.query(CustomerVisit), CustomerVisit, auth_info, db)
    visit_stats = visit_q.with_entities(
        func.count(CustomerVisit.id).label("total"),
        func.sum(case((CustomerVisit.status == "Completed", 1), else_=0)).label("completed_visits"),
        func.sum(case((CustomerVisit.status == "InProgress", 1), else_=0)).label("active_visits"),
    ).first()

    # 7. Geo Summary: checked_in_employees via single subquery & location status list
    max_geo_subq = (
        db.query(func.max(GeoTracking.id).label("max_id"))
        .group_by(GeoTracking.employee_id)
        .subquery()
    )
    latest_geo_q = apply_scope(
        db.query(GeoTracking).join(max_geo_subq, GeoTracking.id == max_geo_subq.c.max_id),
        GeoTracking,
        auth_info,
        db
    )
    checked_in_employees = latest_geo_q.filter(GeoTracking.type == "CheckIn").count()

    latest_geos = (
        latest_geo_q
        .order_by(GeoTracking.timestamp.desc())
        .limit(10)
        .all()
    )
    employee_location_status = [
        {
            "employee_id": g.employee_id,
            "employee_name": g.employee.name if g.employee else f"Employee #{g.employee_id}",
            "type": g.type,
            "latitude": float(g.latitude) if g.latitude is not None else None,
            "longitude": float(g.longitude) if g.longitude is not None else None,
            "timestamp": g.timestamp.isoformat() if g.timestamp else None,
        }
        for g in latest_geos
    ]

    # 8. Upcoming meetings (next 5)
    meet_q = apply_scope(db.query(Meeting), Meeting, auth_info, db)
    upcoming_meetings_count = meet_q.filter(Meeting.date >= today, Meeting.status == "Scheduled").count()
    meetings_5 = (
        meet_q.filter(Meeting.date >= today, Meeting.status == "Scheduled")
        .order_by(Meeting.date.asc(), Meeting.start_time.asc())
        .limit(5)
        .all()
    )
    upcoming_meetings_list = [
        {
            "id": m.id,
            "subject": m.subject,
            "date": m.date.isoformat() if m.date else None,
            "start_time": m.start_time.isoformat() if m.start_time else None,
            "end_time": m.end_time.isoformat() if m.end_time else None,
            "location": m.location,
            "employee_id": m.employee_id,
            "employee_name": m.employee.name if m.employee else None,
        }
        for m in meetings_5
    ]

    # 9. Recent activities (last 10)
    act_q = apply_scope(db.query(Activity), Activity, auth_info, db)
    activities_10 = act_q.order_by(Activity.id.desc()).limit(10).all()
    recent_activities = [
        {
            "id": a.id,
            "type": a.type,
            "related_to_entity": a.related_to_entity,
            "related_to_id": a.related_to_id,
            "description": a.description,
            "date": a.date.isoformat() if a.date else None,
            "employee_id": a.employee_id,
            "employee_name": a.employee.name if a.employee else None,
        }
        for a in activities_10
    ]

    return DashboardSummary(
        total_leads=lead_stats.total or 0,
        new_leads=lead_stats.new_leads or 0,
        contacted_leads=lead_stats.contacted_leads or 0,
        qualified_leads=lead_stats.qualified_leads or 0,
        disqualified_leads=lead_stats.disqualified_leads or 0,

        total_customers=cust_stats.total or 0,
        new_customers=cust_stats.new_customers or 0,
        active_customers=cust_stats.active_customers or 0,

        total_opportunities=opp_stats.total or 0,
        won_opportunities=opp_stats.won_opps or 0,
        lost_opportunities=opp_stats.lost_opps or 0,
        total_expected_revenue=float(opp_stats.total_expected_revenue or 0.0),
        total_won_revenue=float(opp_stats.total_won_revenue or 0.0),
        pipeline_value=float(opp_stats.pipeline_value or 0.0),
        opportunities_by_stage=opportunities_by_stage,

        total_employees=emp_stats.total or 0,
        active_employees=emp_stats.active_employees or 0,
        inactive_employees=emp_stats.inactive_employees or 0,

        pending_tasks=task_stats.pending_tasks or 0,
        completed_tasks=task_stats.completed_tasks or 0,
        overdue_tasks=task_stats.overdue_tasks or 0,

        upcoming_meetings=upcoming_meetings_count,
        upcoming_meetings_list=upcoming_meetings_list,

        completed_visits=visit_stats.completed_visits or 0,
        active_visits=visit_stats.active_visits or 0,
        checked_in_employees=checked_in_employees,
        employee_location_status=employee_location_status,

        recent_activities=recent_activities,
    )

@router.get("/charts", response_model=DashboardCharts)
def get_dashboard_charts(
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Dashboard", "View"))
):
    leads_q = apply_scope(db.query(Lead.status, func.count(Lead.id)), Lead, auth_info, db).group_by(Lead.status).all()
    opp_q = apply_scope(db.query(Opportunity.stage, func.sum(Opportunity.expected_value)), Opportunity, auth_info, db).group_by(Opportunity.stage).all()
    
    scope = auth_info.get("scope", "Own")
    curr_user = auth_info["user"]

    perf_query = db.query(Employee.name, func.sum(Opportunity.expected_value)).join(
        Opportunity, Opportunity.assigned_employee_id == Employee.id
    ).filter(Opportunity.stage == "Won")

    if scope == "Own":
        perf_query = perf_query.filter(Opportunity.assigned_employee_id == curr_user.id)
    elif scope == "Team":
        perf_query = perf_query.filter(Opportunity.assigned_employee_id.in_(get_team_employee_ids(db, curr_user.id)))
    elif scope == "Company":
        perf_query = perf_query.filter(Employee.company_id == curr_user.company_id)

    emp_perf = perf_query.group_by(Employee.name).all()

    # Calculate monthly sales for the current year
    current_year = datetime.now().year
    sales_query = db.query(
        func.month(Opportunity.expected_close_date).label('month'),
        func.sum(Opportunity.expected_value).label('total')
    ).filter(
        Opportunity.stage == "Won",
        func.year(Opportunity.expected_close_date) == current_year
    )

    if scope == "Own":
        sales_query = sales_query.filter(Opportunity.assigned_employee_id == curr_user.id)
    elif scope == "Team":
        sales_query = sales_query.filter(Opportunity.assigned_employee_id.in_(get_team_employee_ids(db, curr_user.id)))
    elif scope == "Company":
        sales_query = sales_query.join(Employee, Opportunity.assigned_employee_id == Employee.id).filter(Employee.company_id == curr_user.company_id)

    sales_data = sales_query.group_by(func.month(Opportunity.expected_close_date)).all()
    
    # Map months to strings
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_sales_data = []
    sales_dict = {row.month: row.total for row in sales_data if row.month}
    for i in range(1, 13):
        monthly_sales_data.append(ChartDataPoint(label=months[i-1], value=float(sales_dict.get(i, 0) or 0)))

    pipeline_stages = ["Opportunity", "Proposal", "Negotiation", "Won", "Lost"]
    opp_dict = {k: float(v or 0) for k, v in opp_q if k}
    opp_distribution = [
        ChartDataPoint(label=stage, value=opp_dict.get(stage, 0.0))
        for stage in pipeline_stages
    ]
    for k, v in opp_dict.items():
        if k not in pipeline_stages:
            opp_distribution.append(ChartDataPoint(label=k, value=v))

    return DashboardCharts(
        lead_distribution=[ChartDataPoint(label=k, value=float(v or 0)) for k, v in leads_q if k],
        opportunity_distribution=opp_distribution,
        monthly_sales=monthly_sales_data,
        employee_performance=[ChartDataPoint(label=k, value=float(v or 0)) for k, v in emp_perf if k]
    )