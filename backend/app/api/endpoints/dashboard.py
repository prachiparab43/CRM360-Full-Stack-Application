from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.api import deps
from app.models.domain import Lead, Opportunity, Customer, Employee, Task, Meeting, CustomerVisit
from app.schemas.dashboard import DashboardSummary, DashboardCharts, ChartDataPoint

router = APIRouter()

from fastapi import HTTPException
from app.models.domain import Contact

def apply_scope(query, model, auth_info):
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    if scope == "All":
        return query
        
    emp_col = None
    if model == Contact:
        # Avoid duplicate join if Customer already joined
        if 'Customer' not in str(query):
            query = query.join(Customer, Contact.customer_id == Customer.id)
        emp_col = Customer.assigned_employee_id
    elif hasattr(model, 'assigned_employee_id'): 
        emp_col = model.assigned_employee_id
    elif hasattr(model, 'employee_id'): 
        emp_col = model.employee_id
    elif model == Employee: 
        emp_col = model.id
        
    if emp_col is None:
        raise HTTPException(status_code=403, detail=f"Cannot apply RBAC scope to model {model.__name__}")

    if scope == "Own":
        return query.filter(emp_col == curr_user.id)
    elif scope in ["Team", "Company"]:
        if model != Employee and 'Employee' not in str(query):
            query = query.join(Employee, emp_col == Employee.id)
        return query.filter(Employee.company_id == curr_user.company_id)
    
    raise HTTPException(status_code=403, detail="Invalid scope type")
        
    # Find employee column mapping
    emp_col = None
    if hasattr(model, 'assigned_employee_id'): emp_col = model.assigned_employee_id
    elif hasattr(model, 'employee_id'): emp_col = model.employee_id
    elif model == Employee: emp_col = model.id

    if scope == "Own" and emp_col is not None:
        return query.filter(emp_col == curr_user.id)
    elif scope in ["Team", "Company"] and emp_col is not None:
        if model != Employee:
            query = query.join(Employee, emp_col == Employee.id)
        return query.filter(Employee.company_id == curr_user.company_id)
    return query

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Dashboard", "View"))
):
    leads_q = apply_scope(db.query(Lead), Lead, auth_info)
    opp_q = apply_scope(db.query(Opportunity), Opportunity, auth_info)
    cust_q = apply_scope(db.query(Customer), Customer, auth_info)
    emp_q = apply_scope(db.query(Employee), Employee, auth_info)
    task_q = apply_scope(db.query(Task), Task, auth_info)
    meet_q = apply_scope(db.query(Meeting), Meeting, auth_info)
    visit_q = apply_scope(db.query(CustomerVisit), CustomerVisit, auth_info)

    today = datetime.now().date()

    return DashboardSummary(
        total_leads=leads_q.count(),
        total_customers=cust_q.count(),
        total_opportunities=opp_q.count(),
        total_employees=emp_q.count(),
        active_employees=emp_q.filter(Employee.status == "Active").count(),
        inactive_employees=emp_q.filter(Employee.status != "Active").count(),
        qualified_leads=leads_q.filter(Lead.status == "Qualified").count(),
        disqualified_leads=leads_q.filter(Lead.status == "Disqualified").count(),
        won_opportunities=opp_q.filter(Opportunity.stage == "Won").count(),
        lost_opportunities=opp_q.filter(Opportunity.stage == "Lost").count(),
        total_expected_revenue=db.query(func.sum(Opportunity.expected_value)).filter(Opportunity.id.in_(opp_q.with_entities(Opportunity.id))).scalar() or 0.0,
        total_won_revenue=db.query(func.sum(Opportunity.expected_value)).filter(Opportunity.id.in_(opp_q.with_entities(Opportunity.id)), Opportunity.stage == "Won").scalar() or 0.0,
        pending_tasks=task_q.filter(Task.status == "Pending").count(),
        completed_tasks=task_q.filter(Task.status == "Completed").count(),
        overdue_tasks=task_q.filter(Task.due_date < today, Task.status.notin_(["Completed", "Cancelled"])).count(),
        upcoming_meetings=meet_q.filter(Meeting.date >= today, Meeting.status == "Scheduled").count(),
        completed_visits=visit_q.filter(CustomerVisit.status == "Completed").count(),
    )

@router.get("/charts", response_model=DashboardCharts)
def get_dashboard_charts(
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Dashboard", "View"))
):
    leads_q = apply_scope(db.query(Lead.status, func.count(Lead.id)), Lead, auth_info).group_by(Lead.status).all()
    opp_q = apply_scope(db.query(Opportunity.stage, func.count(Opportunity.id)), Opportunity, auth_info).group_by(Opportunity.stage).all()
    
    perf_query = apply_scope(db.query(Employee.name, func.sum(Opportunity.expected_value)), Opportunity, auth_info).filter(Opportunity.stage == "Won")
    if 'Employee' not in str(perf_query):
        perf_query = perf_query.join(Employee, Opportunity.assigned_employee_id == Employee.id)
    emp_perf = perf_query.group_by(Employee.name).all()

    # Calculate monthly sales for the current year
    current_year = datetime.now().year
    sales_query = apply_scope(
        db.query(
            func.month(Opportunity.expected_close_date).label('month'),
            func.sum(Opportunity.expected_value).label('total')
        ), Opportunity, auth_info
    ).filter(
        Opportunity.stage == "Won",
        func.year(Opportunity.expected_close_date) == current_year
    ).group_by(func.month(Opportunity.expected_close_date)).all()
    
    # Map months to strings
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_sales_data = []
    sales_dict = {row.month: row.total for row in sales_query if row.month}
    for i in range(1, 13):
        monthly_sales_data.append(ChartDataPoint(label=months[i-1], value=sales_dict.get(i, 0)))

    return DashboardCharts(
        lead_distribution=[ChartDataPoint(label=k, value=v
) for k, v in leads_q],
        opportunity_distribution=[ChartDataPoint(label=k, value=v) for k, v in opp_q],
        monthly_sales=monthly_sales_data,
        employee_performance=[ChartDataPoint(label=k, value=v or 0) for k, v in emp_perf]
    )