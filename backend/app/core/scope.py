"""CRM360 RBAC Data Scope Resolution.

Enforces Own, Team, Company, and All data scopes across all entities.
Team scope computes the recursive reporting hierarchy (user + direct/indirect reports)
via a SQL Server recursive CTE, cached per database session.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

from app.models.domain import (
    Lead, Opportunity, Customer, Contact,
    Activity, Task, Meeting, CustomerVisit,
    GeoTracking, Employee, Company, AuditLog
)

def get_team_employee_ids(db: Session, user_id: int) -> List[int]:
    """
    Returns the user ID plus all direct and indirect subordinate employee IDs
    using a recursive CTE, cached per request in db.info.
    """
    if db is None:
        return [user_id]
        
    cache = getattr(db, "info", {}).setdefault("_team_cache", {})
    if user_id in cache:
        return cache[user_id]
        
    try:
        query = text("""
            WITH TeamCTE AS (
                SELECT id FROM employees WHERE id = :user_id
                UNION ALL
                SELECT e.id FROM employees e
                INNER JOIN TeamCTE t ON e.manager_id = t.id
            )
            SELECT id FROM TeamCTE
        """)
        team_ids = [int(r) for r in db.execute(query, {"user_id": user_id}).scalars().all()]
        if not team_ids:
            team_ids = [user_id]
    except Exception:
        # Fallback in Python if CTE unsupported (e.g. SQLite test setup)
        team_ids = [user_id]
        queue = [user_id]
        while queue:
            cur = queue.pop(0)
            subs = [e.id for e in db.query(Employee.id).filter(Employee.manager_id == cur).all()]
            for s in subs:
                if s not in team_ids:
                    team_ids.append(s)
                    queue.append(s)

    cache[user_id] = team_ids
    return team_ids

def scope_lead(query, auth_info: dict, db: Session):
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    if scope == "Own":
        return query.filter(Lead.assigned_employee_id == curr_user.id)
    elif scope == "Team":
        return query.filter(Lead.assigned_employee_id.in_(get_team_employee_ids(db, curr_user.id)))
    elif scope == "Company":
        return query.join(Employee, Lead.assigned_employee_id == Employee.id).filter(Employee.company_id == curr_user.company_id)
    return query

def scope_opportunity(query, auth_info: dict, db: Session):
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    if scope == "Own":
        return query.filter(Opportunity.assigned_employee_id == curr_user.id)
    elif scope == "Team":
        return query.filter(Opportunity.assigned_employee_id.in_(get_team_employee_ids(db, curr_user.id)))
    elif scope == "Company":
        return query.join(Employee, Opportunity.assigned_employee_id == Employee.id).filter(Employee.company_id == curr_user.company_id)
    return query

def scope_customer(query, auth_info: dict, db: Session):
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    if scope == "Own":
        return query.filter(Customer.assigned_employee_id == curr_user.id)
    elif scope == "Team":
        return query.filter(Customer.assigned_employee_id.in_(get_team_employee_ids(db, curr_user.id)))
    elif scope == "Company":
        return query.join(Employee, Customer.assigned_employee_id == Employee.id).filter(Employee.company_id == curr_user.company_id)
    return query

def scope_contact(query, auth_info: dict, db: Session):
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    if scope == "Own":
        return query.join(Customer, Contact.customer_id == Customer.id).filter(Customer.assigned_employee_id == curr_user.id)
    elif scope == "Team":
        return query.join(Customer, Contact.customer_id == Customer.id).filter(Customer.assigned_employee_id.in_(get_team_employee_ids(db, curr_user.id)))
    elif scope == "Company":
        return query.join(Customer, Contact.customer_id == Customer.id).join(Employee, Customer.assigned_employee_id == Employee.id).filter(Employee.company_id == curr_user.company_id)
    return query

def scope_activity(query, auth_info: dict, db: Session):
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    if scope == "Own":
        return query.filter(Activity.employee_id == curr_user.id)
    elif scope == "Team":
        return query.filter(Activity.employee_id.in_(get_team_employee_ids(db, curr_user.id)))
    elif scope == "Company":
        return query.join(Employee, Activity.employee_id == Employee.id).filter(Employee.company_id == curr_user.company_id)
    return query

def scope_task(query, auth_info: dict, db: Session):
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    if scope == "Own":
        return query.filter(Task.assigned_employee_id == curr_user.id)
    elif scope == "Team":
        return query.filter(Task.assigned_employee_id.in_(get_team_employee_ids(db, curr_user.id)))
    elif scope == "Company":
        return query.join(Employee, Task.assigned_employee_id == Employee.id).filter(Employee.company_id == curr_user.company_id)
    return query

def scope_meeting(query, auth_info: dict, db: Session):
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    if scope == "Own":
        return query.filter(Meeting.employee_id == curr_user.id)
    elif scope == "Team":
        return query.filter(Meeting.employee_id.in_(get_team_employee_ids(db, curr_user.id)))
    elif scope == "Company":
        return query.join(Employee, Meeting.employee_id == Employee.id).filter(Employee.company_id == curr_user.company_id)
    return query

def scope_visit(query, auth_info: dict, db: Session):
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    if scope == "Own":
        return query.filter(CustomerVisit.employee_id == curr_user.id)
    elif scope == "Team":
        return query.filter(CustomerVisit.employee_id.in_(get_team_employee_ids(db, curr_user.id)))
    elif scope == "Company":
        return query.join(Employee, CustomerVisit.employee_id == Employee.id).filter(Employee.company_id == curr_user.company_id)
    return query

def scope_geo(query, auth_info: dict, db: Session):
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    if scope == "Own":
        return query.filter(GeoTracking.employee_id == curr_user.id)
    elif scope == "Team":
        return query.filter(GeoTracking.employee_id.in_(get_team_employee_ids(db, curr_user.id)))
    elif scope == "Company":
        return query.join(Employee, GeoTracking.employee_id == Employee.id).filter(Employee.company_id == curr_user.company_id)
    return query

def scope_employee(query, auth_info: dict, db: Session):
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    if scope == "Own":
        return query.filter(Employee.id == curr_user.id)
    elif scope == "Team":
        return query.filter(Employee.id.in_(get_team_employee_ids(db, curr_user.id)))
    elif scope == "Company":
        return query.filter(Employee.company_id == curr_user.company_id)
    return query

def scope_company(query, auth_info: dict, db: Session):
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    if scope in ["Own", "Team", "Company"]:
        return query.filter(Company.id == curr_user.company_id)
    return query

def scope_audit_log(query, auth_info: dict, db: Session):
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    if scope == "Own":
        return query.filter(AuditLog.user_id == curr_user.id)
    elif scope == "Team":
        return query.filter(AuditLog.user_id.in_(get_team_employee_ids(db, curr_user.id)))
    elif scope == "Company":
        return query.join(Employee, AuditLog.user_id == Employee.id).filter(Employee.company_id == curr_user.company_id)
    return query

MODEL_SCOPERS = {
    Lead: scope_lead,
    Opportunity: scope_opportunity,
    Customer: scope_customer,
    Contact: scope_contact,
    Activity: scope_activity,
    Task: scope_task,
    Meeting: scope_meeting,
    CustomerVisit: scope_visit,
    GeoTracking: scope_geo,
    Employee: scope_employee,
    Company: scope_company,
    AuditLog: scope_audit_log,
}

def apply_scope(query, model, auth_info: dict, db: Optional[Session] = None):
    """
    Applies the authorized data scope (Own, Team, Company, All) to a SQLAlchemy query.
    """
    scope = auth_info.get("scope", "Own")
    if scope == "All":
        return query
        
    if db is None:
        db = getattr(query, "session", None)
        
    scoper = MODEL_SCOPERS.get(model)
    if scoper:
        return scoper(query, auth_info, db)
        
    raise HTTPException(status_code=403, detail=f"Cannot apply RBAC scope to model {model.__name__}")
