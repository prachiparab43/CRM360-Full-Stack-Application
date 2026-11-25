import json
from datetime import date, datetime
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api import deps
from app.core.scope import apply_scope, get_team_employee_ids
from app.models.domain import Opportunity, Customer, Employee, Lead, Contact, AuditLog
from app.schemas.opportunity import (
    OpportunityCreate, OpportunityUpdate, OpportunityStageUpdate, OpportunityResponse
)
from app.schemas.audit import AuditLogResponse
from app.core.audit import log_action
from app.core.pagination import paginate_query

router = APIRouter()

ALLOWED_OPP_SORT_FIELDS = [
    "id", "name", "expected_value", "probability", "expected_close_date", "stage", "created_date"
]

@router.post("/", response_model=OpportunityResponse)
def create_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_in: OpportunityCreate,
    request: Request,
    auth_info: dict = Depends(deps.PermissionChecker("Opportunity", "Create")),
):
    if opp_in.expected_close_date and opp_in.expected_close_date < date.today():
        raise HTTPException(status_code=400, detail="Expected close date cannot be before creation date.")

    db_opp = Opportunity(**opp_in.model_dump())
    db.add(db_opp)
    db.flush()
    
    log_action(
        db,
        auth_info["user"].id,
        "Create",
        "Opportunity",
        db_opp.id,
        new_val={"name": db_opp.name, "expected_value": db_opp.expected_value, "stage": db_opp.stage},
        request=request
    )
    db.commit()
    db.refresh(db_opp)
    return db_opp

@router.get("/")
def get_opportunities(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    stage: Optional[str] = None,
    sort_by: Optional[str] = "id",
    sort_dir: Optional[str] = "desc",
    paginate: bool = True,
    raw: bool = False,
    auth_info: dict = Depends(deps.PermissionChecker("Opportunity", "View")),
):
    query = apply_scope(db.query(Opportunity), Opportunity, auth_info, db)
        
    if search:
        query = query.filter(Opportunity.name.contains(search))
    if stage:
        query = query.filter(Opportunity.stage == stage)
        
    res = paginate_query(
        query=query,
        model=Opportunity,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
        allowed_sort_fields=ALLOWED_OPP_SORT_FIELDS,
        default_sort_field="id",
        default_sort_dir="desc",
        paginate=paginate,
        raw=raw,
    )
    if isinstance(res, dict) and "items" in res:
        res["items"] = [OpportunityResponse.model_validate(item) for item in res["items"]]
    elif isinstance(res, list):
        res = [OpportunityResponse.model_validate(item) for item in res]
    return res

@router.get("/{opp_id}", response_model=OpportunityResponse)
def get_opportunity(
    opp_id: int,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Opportunity", "View")),
):
    opp = apply_scope(db.query(Opportunity).filter(Opportunity.id == opp_id), Opportunity, auth_info, db).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp

@router.put("/{opp_id}", response_model=OpportunityResponse)
def update_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    opp_in: OpportunityUpdate,
    request: Request,
    auth_info: dict = Depends(deps.PermissionChecker("Opportunity", "Edit")),
):
    opp = apply_scope(db.query(Opportunity).filter(Opportunity.id == opp_id), Opportunity, auth_info, db).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    if opp.stage in ["Won", "Lost"]:
        raise HTTPException(status_code=400, detail="Cannot edit a Won or Lost opportunity.")

    update_data = opp_in.model_dump(exclude_unset=True)

    # Validate close date if changed
    if "expected_close_date" in update_data and update_data["expected_close_date"] is not None:
        creation_date = opp.created_date.date() if opp.created_date else date.today()
        if update_data["expected_close_date"] < creation_date:
            raise HTTPException(status_code=400, detail="Expected close date cannot be before creation date.")

    # Reassignment permission and scope check
    old_assigned = opp.assigned_employee_id
    if "assigned_employee_id" in update_data and update_data["assigned_employee_id"] != old_assigned:
        reassign_perm = deps.PermissionChecker("Opportunity", "Reassign Opportunity")(auth_info["user"], db)
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

    old_vals = {}
    new_vals = {}
    for field, value in update_data.items():
        current_val = getattr(opp, field)
        if current_val != value:
            old_vals[field] = str(current_val) if isinstance(current_val, (date, datetime)) else current_val
            new_vals[field] = str(value) if isinstance(value, (date, datetime)) else value
            setattr(opp, field, value)
        
    action_name = "Reassign" if ("assigned_employee_id" in update_data and update_data["assigned_employee_id"] != old_assigned) else "Edit"
    log_action(
        db,
        auth_info["user"].id,
        action_name,
        "Opportunity",
        opp.id,
        old_val=old_vals,
        new_val=new_vals,
        request=request
    )
    db.commit()
    db.refresh(opp)
    return opp

@router.post("/{opp_id}/stage", response_model=OpportunityResponse)
def change_stage(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    stage_in: OpportunityStageUpdate,
    request: Request,
    auth_info: dict = Depends(deps.PermissionChecker("Opportunity", "View")),
):
    opp = apply_scope(db.query(Opportunity).filter(Opportunity.id == opp_id), Opportunity, auth_info, db).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    if opp.stage in ["Won", "Lost"]:
        raise HTTPException(status_code=400, detail="Cannot change stage of a Won or Lost opportunity.")

    # Lifecycle transitions: Opportunity -> Proposal -> Negotiation -> Won/Lost
    # Direct Opportunity -> Won is strictly disallowed.
    # Direct Proposal -> Won is strictly disallowed.
    # Lost is allowed from any open stage.
    VALID_TRANSITIONS = {
        "Opportunity": ["Proposal", "Lost"],
        "Proposal": ["Negotiation", "Lost"],
        "Negotiation": ["Won", "Lost"]
    }
    
    if stage_in.stage not in VALID_TRANSITIONS.get(opp.stage, []):
        raise HTTPException(status_code=400, detail=f"Invalid transition from {opp.stage} to {stage_in.stage}")

    # Enforce distinct permissions per stage
    if stage_in.stage == "Won":
        deps.PermissionChecker("Opportunity", "Mark Opportunity Won")(auth_info["user"], db)
    elif stage_in.stage == "Lost":
        deps.PermissionChecker("Opportunity", "Mark Opportunity Lost")(auth_info["user"], db)
    else:
        deps.PermissionChecker("Opportunity", "Change Opportunity Stage")(auth_info["user"], db)

    old_stage = opp.stage
    old_vals = {"stage": old_stage, "probability": opp.probability}

    if stage_in.stage == "Lost":
        if not stage_in.lost_reason or not stage_in.lost_reason.strip():
            raise HTTPException(status_code=400, detail="Lost Reason is required when marking opportunity as Lost.")
        opp.lost_reason = stage_in.lost_reason
        opp.probability = 0.0

    elif stage_in.stage == "Won":
        opp.probability = 100.0
        try:
            # 1. Determine company of opportunity
            opp_emp = db.query(Employee).filter(Employee.id == opp.assigned_employee_id).first() if opp.assigned_employee_id else None
            opp_company_id = opp_emp.company_id if opp_emp else auth_info["user"].company_id

            # 2. Determine customer name from lead company/name or opportunity name
            lead = db.query(Lead).filter(Lead.id == opp.lead_id).first() if opp.lead_id else None
            if lead and lead.company:
                customer_name = lead.company.strip()
            elif lead and lead.name:
                customer_name = lead.name.strip()
            else:
                customer_name = opp.name.replace(" - Opportunity", "").strip()

            # 3. Create or update Customer scoped to the opportunity's company (never match across companies)
            customer = (
                db.query(Customer)
                .join(Employee, Customer.assigned_employee_id == Employee.id)
                .filter(Employee.company_id == opp_company_id, Customer.name == customer_name)
                .first()
            )
            if not customer:
                customer = Customer(
                    name=customer_name,
                    address=lead.requirement if lead else None,
                    phone=lead.phone if lead else None,
                    email=lead.email if lead else None,
                    assigned_employee_id=opp.assigned_employee_id or auth_info["user"].id,
                    status="Active"
                )
                db.add(customer)
                db.flush()
            else:
                # Update existing customer info if missing
                if lead and not customer.email and lead.email:
                    customer.email = lead.email
                if lead and not customer.phone and lead.phone:
                    customer.phone = lead.phone

            # 4. Copy lead's contact into Contacts table
            if lead:
                contact_name = lead.contact_name or lead.name
                if contact_name:
                    existing_contact = db.query(Contact).filter(
                        Contact.customer_id == customer.id,
                        (Contact.email == lead.email) if lead.email else (Contact.name == contact_name)
                    ).first()
                    if not existing_contact:
                        contact = Contact(
                            name=contact_name,
                            customer_id=customer.id,
                            email=lead.email,
                            phone=lead.phone,
                            status="Active",
                            notes=lead.notes
                        )
                        db.add(contact)
                        db.flush()

            # 5. Link opportunity.customer_id and keep lead<->opportunity link
            opp.customer_id = customer.id

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Transaction failed during customer creation: " + str(e))

    opp.stage = stage_in.stage
    new_vals = {"stage": opp.stage, "probability": opp.probability, "customer_id": opp.customer_id, "lost_reason": opp.lost_reason}

    action_label = (
        "Mark Opportunity Won" if opp.stage == "Won"
        else "Mark Opportunity Lost" if opp.stage == "Lost"
        else "Change Opportunity Stage"
    )
    log_action(
        db,
        auth_info["user"].id,
        action_label,
        "Opportunity",
        opp.id,
        old_val=old_vals,
        new_val=new_vals,
        request=request
    )
    db.commit()
    db.refresh(opp)
    return opp

@router.get("/{opp_id}/history", response_model=List[AuditLogResponse])
def get_opportunity_history(
    opp_id: int,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Opportunity", "View")),
):
    opp = apply_scope(db.query(Opportunity).filter(Opportunity.id == opp_id), Opportunity, auth_info, db).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    logs = (
        db.query(AuditLog)
        .filter(AuditLog.module == "Opportunity", AuditLog.record_id == opp_id)
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
