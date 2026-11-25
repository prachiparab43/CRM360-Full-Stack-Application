import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Any
from datetime import datetime, date

from app.api import deps
from app.core.scope import apply_scope, get_team_employee_ids
from app.models.domain import Lead, Opportunity, Employee, AuditLog, Customer
from app.schemas.lead import (
    LeadCreate, LeadUpdate, LeadResponse, LeadQualify, LeadDisqualify, LeadConvert
)
from app.schemas.audit import AuditLogResponse
from app.core.audit import log_action
from app.core.pagination import paginate_query

router = APIRouter()

ALLOWED_LEAD_SORT_FIELDS = [
    "id", "name", "company", "status", "lead_source", "created_date"
]

def _check_lead_duplicate(db: Session, email: Optional[str], phone: Optional[str], exclude_id: Optional[int] = None) -> Optional[str]:
    conds = []
    if email and email.strip():
        conds.append(Lead.email == email.strip())
    if phone and phone.strip():
        conds.append(Lead.phone == phone.strip())
    if not conds:
        return None

    q = db.query(Lead).filter(or_(*conds))
    if exclude_id:
        q = q.filter(Lead.id != exclude_id)
    dup = q.first()
    if dup:
        return f"Duplicate lead warning: Lead '{dup.name}' (ID: {dup.id}) already exists with matching email or phone."
    return None

@router.post("/", response_model=LeadResponse)
def create_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_in: LeadCreate,
    request: Request,
    response: Response,
    auth_info: dict = Depends(deps.PermissionChecker("Lead", "Create")),
):
    warning_msg = _check_lead_duplicate(db, lead_in.email, lead_in.phone)
    if warning_msg:
        response.headers["X-Duplicate-Lead-Warning"] = warning_msg

    db_lead = Lead(**lead_in.model_dump())
    db.add(db_lead)
    db.flush()
    
    log_action(
        db,
        auth_info["user"].id,
        "Create",
        "Lead",
        db_lead.id,
        new_val={"name": db_lead.name, "company": db_lead.company, "status": db_lead.status},
        request=request
    )
    db.commit()
    db.refresh(db_lead)

    res_data = LeadResponse.model_validate(db_lead)
    res_data.warning = warning_msg
    return res_data

@router.get("/")
def get_leads(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: Optional[str] = "id",
    sort_dir: Optional[str] = "desc",
    paginate: bool = True,
    raw: bool = False,
    auth_info: dict = Depends(deps.PermissionChecker("Lead", "View")),
):
    query = apply_scope(db.query(Lead), Lead, auth_info, db)
        
    if search:
        query = query.filter(Lead.name.contains(search) | Lead.company.contains(search))
    if status:
        query = query.filter(Lead.status == status)
        
    res = paginate_query(
        query=query,
        model=Lead,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
        allowed_sort_fields=ALLOWED_LEAD_SORT_FIELDS,
        default_sort_field="id",
        default_sort_dir="desc",
        paginate=paginate,
        raw=raw,
    )
    if isinstance(res, dict) and "items" in res:
        res["items"] = [LeadResponse.model_validate(item) for item in res["items"]]
    elif isinstance(res, list):
        res = [LeadResponse.model_validate(item) for item in res]
    return res

@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(
    lead_id: int,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Lead", "View")),
):
    lead = apply_scope(db.query(Lead).filter(Lead.id == lead_id), Lead, auth_info, db).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.put("/{lead_id}", response_model=LeadResponse)
def update_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    lead_in: LeadUpdate,
    request: Request,
    response: Response,
    auth_info: dict = Depends(deps.PermissionChecker("Lead", "Edit")),
):
    lead = apply_scope(db.query(Lead).filter(Lead.id == lead_id), Lead, auth_info, db).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    # Enforce valid transitions if status is updated manually
    if lead_in.status and lead_in.status not in ["New", "Contacted", "Closed"]:
        if lead_in.status in ["Qualified", "Disqualified"]:
            raise HTTPException(status_code=400, detail="Use specific endpoints for qualification/disqualification.")

    update_data = lead_in.model_dump(exclude_unset=True)
    old_assigned = lead.assigned_employee_id

    # Reassign check
    if "assigned_employee_id" in update_data and update_data["assigned_employee_id"] != old_assigned:
        reassign_perm = deps.PermissionChecker("Lead", "Reassign Lead")(auth_info["user"], db)
        target_emp_id = update_data["assigned_employee_id"]
        if target_emp_id is not None:
            target_emp = db.query(Employee).filter(Employee.id == target_emp_id).first()
            if not target_emp:
                raise HTTPException(status_code=404, detail="Target employee not found")
            scope = reassign_perm["scope"]
            curr_user = auth_info["user"]
            if scope == "Own" and target_emp.id != curr_user.id:
                raise HTTPException(status_code=403, detail="Target employee is outside of authorized data scope.")
            elif scope == "Team" and target_emp.id not in get_team_employee_ids(db, curr_user.id):
                raise HTTPException(status_code=403, detail="Target employee is outside of authorized data scope.")
            elif scope == "Company" and target_emp.company_id != curr_user.company_id:
                raise HTTPException(status_code=403, detail="Target employee is outside of authorized data scope.")

    warning_msg = _check_lead_duplicate(db, update_data.get("email"), update_data.get("phone"), exclude_id=lead.id)
    if warning_msg:
        response.headers["X-Duplicate-Lead-Warning"] = warning_msg

    old_vals = {}
    new_vals = {}
    for field, value in update_data.items():
        current_val = getattr(lead, field)
        if current_val != value:
            old_vals[field] = str(current_val) if isinstance(current_val, (date, datetime)) else current_val
            new_vals[field] = str(value) if isinstance(value, (date, datetime)) else value
            setattr(lead, field, value)
        
    action_name = "Reassign" if ("assigned_employee_id" in update_data and update_data["assigned_employee_id"] != old_assigned) else "Edit"
    log_action(
        db,
        auth_info["user"].id,
        action_name,
        "Lead",
        lead.id,
        old_val=old_vals,
        new_val=new_vals,
        request=request
    )
    db.commit()
    db.refresh(lead)

    res_data = LeadResponse.model_validate(lead)
    res_data.warning = warning_msg
    return res_data

@router.post("/{lead_id}/qualify", response_model=LeadResponse)
def qualify_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    qualify_in: Optional[LeadQualify] = None,
    request: Request = None,
    auth_info: dict = Depends(deps.PermissionChecker("Lead", "Qualify Lead")),
):
    lead = apply_scope(db.query(Lead).filter(Lead.id == lead_id), Lead, auth_info, db).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.status in ["Qualified", "Closed", "Disqualified"]:
        raise HTTPException(status_code=400, detail=f"Cannot qualify a lead with status '{lead.status}'.")

    exp_val = qualify_in.expected_value if qualify_in and qualify_in.expected_value is not None else 0.0
    prob_val = qualify_in.probability if qualify_in and qualify_in.probability is not None else 0.0

    if exp_val < 0:
        raise HTTPException(status_code=400, detail="Expected value must be >= 0.")
    if prob_val < 0 or prob_val > 100:
        raise HTTPException(status_code=400, detail="Probability must be between 0 and 100.")

    try:
        old_status = lead.status
        lead.status = "Qualified"
        
        # Create Opportunity
        opp = Opportunity(
            name=f"{lead.company or lead.name} - Opportunity",
            lead_id=lead.id,
            expected_value=exp_val,
            probability=prob_val,
            assigned_employee_id=lead.assigned_employee_id,
            stage="Opportunity"
        )
        db.add(opp)
        db.flush()
        
        log_action(
            db,
            auth_info["user"].id,
            "Qualify Lead",
            "Lead",
            lead.id,
            old_val={"status": old_status},
            new_val={"status": "Qualified", "opportunity_id": opp.id},
            request=request
        )
        log_action(
            db,
            auth_info["user"].id,
            "Create",
            "Opportunity",
            opp.id,
            new_val={"name": opp.name, "lead_id": lead.id, "stage": "Opportunity"},
            request=request
        )
        db.commit()
        db.refresh(lead)
        return lead
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Transaction failed during qualification: " + str(e))

@router.post("/{lead_id}/convert", response_model=LeadResponse)
def convert_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    convert_in: LeadConvert,
    request: Request,
    auth_info: dict = Depends(deps.PermissionChecker("Lead", "Create Opportunity")),
):
    lead = apply_scope(db.query(Lead).filter(Lead.id == lead_id), Lead, auth_info, db).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    if lead.status == "Disqualified":
        raise HTTPException(status_code=400, detail="Cannot convert a disqualified lead.")

    # Check for duplicate conversion
    existing_opp = db.query(Opportunity).filter(Opportunity.lead_id == lead.id).first()
    if existing_opp:
        raise HTTPException(
            status_code=400,
            detail=f"Lead has already been converted to Opportunity '{existing_opp.name}' (ID: {existing_opp.id})."
        )

    # Validate name
    if not convert_in.name or not convert_in.name.strip():
        raise HTTPException(status_code=400, detail="Opportunity name is required.")

    # Validate close date if supplied
    if convert_in.expected_close_date and convert_in.expected_close_date < date.today():
        raise HTTPException(status_code=400, detail="Expected close date cannot be in the past.")

    # Validate assigned employee scope if supplied
    assigned_emp_id = convert_in.assigned_employee_id or lead.assigned_employee_id or auth_info["user"].id
    if convert_in.assigned_employee_id:
        target_emp = db.query(Employee).filter(Employee.id == convert_in.assigned_employee_id).first()
        if not target_emp:
            raise HTTPException(status_code=404, detail="Assigned employee not found")
        scope = auth_info["scope"]
        curr_user = auth_info["user"]
        if scope == "Own" and target_emp.id != curr_user.id:
            raise HTTPException(status_code=403, detail="Target employee is outside of authorized data scope.")
        elif scope == "Team" and target_emp.id not in get_team_employee_ids(db, curr_user.id):
            raise HTTPException(status_code=403, detail="Target employee is outside of authorized data scope.")
        elif scope == "Company" and target_emp.company_id != curr_user.company_id:
            raise HTTPException(status_code=403, detail="Target employee is outside of authorized data scope.")

    # Validate customer if provided
    if convert_in.customer_id:
        cust = db.query(Customer).filter(Customer.id == convert_in.customer_id).first()
        if not cust:
            raise HTTPException(status_code=404, detail="Customer not found")

    try:
        old_status = lead.status
        lead.status = "Qualified"

        opp = Opportunity(
            name=convert_in.name.strip(),
            lead_id=lead.id,
            customer_id=convert_in.customer_id,
            expected_value=convert_in.expected_value or 0.0,
            probability=convert_in.probability if convert_in.probability is not None else 10.0,
            expected_close_date=convert_in.expected_close_date,
            stage=convert_in.stage or "Opportunity",
            description=convert_in.description or lead.requirement,
            notes=convert_in.notes or lead.notes,
            assigned_employee_id=assigned_emp_id,
        )
        db.add(opp)
        db.flush()

        log_action(
            db,
            auth_info["user"].id,
            "Convert to Opportunity",
            "Lead",
            lead.id,
            old_val={"status": old_status},
            new_val={"status": "Qualified", "opportunity_id": opp.id, "opportunity_name": opp.name},
            request=request
        )
        log_action(
            db,
            auth_info["user"].id,
            "Create",
            "Opportunity",
            opp.id,
            new_val={
                "name": opp.name,
                "lead_id": lead.id,
                "stage": opp.stage,
                "expected_value": opp.expected_value,
                "assigned_employee_id": opp.assigned_employee_id
            },
            request=request
        )
        db.commit()
        db.refresh(lead)
        return lead
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Transaction failed during lead conversion: " + str(e))

@router.post("/{lead_id}/disqualify", response_model=LeadResponse)
def disqualify_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    disqualify_in: LeadDisqualify,
    request: Request,
    auth_info: dict = Depends(deps.PermissionChecker("Lead", "Edit")),
):
    if not disqualify_in.reason or not disqualify_in.reason.strip():
        raise HTTPException(status_code=400, detail="Disqualification reason is required.")
        
    lead = apply_scope(db.query(Lead).filter(Lead.id == lead_id), Lead, auth_info, db).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.status in ["Qualified", "Closed", "Disqualified"]:
        raise HTTPException(status_code=400, detail=f"Cannot disqualify a lead with status '{lead.status}'.")

    old_status = lead.status
    lead.status = "Disqualified"
    lead.disqualified_reason = disqualify_in.reason
    
    log_action(
        db,
        auth_info["user"].id,
        "Disqualify",
        "Lead",
        lead.id,
        old_val={"status": old_status},
        new_val={"status": "Disqualified", "reason": lead.disqualified_reason},
        request=request
    )
    db.commit()
    db.refresh(lead)
    return lead

@router.get("/{lead_id}/history", response_model=List[AuditLogResponse])
def get_lead_history(
    lead_id: int,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Lead", "View")),
):
    lead = apply_scope(db.query(Lead).filter(Lead.id == lead_id), Lead, auth_info, db).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    logs = (
        db.query(AuditLog)
        .filter(AuditLog.module == "Lead", AuditLog.record_id == lead_id)
        .order_by(AuditLog.timestamp.desc())
        .all()
    )
    return [
        AuditLogResponse(
            id=l.id,
            user_id=l.user_id,
            user_name=l.user.name if l.user else None,
            action=l.action,
            module=l.module,
            record_id=l.record_id,
            old_value=l.old_value,
            new_value=l.new_value,
            timestamp=l.timestamp,
            request_info=l.request_info,
        )
        for l in logs
    ]
