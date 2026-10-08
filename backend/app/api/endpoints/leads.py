from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.models.domain import Lead, Opportunity, Employee
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse, LeadQualify, LeadDisqualify
from app.core.audit import log_action

router = APIRouter()

@router.post("/", response_model=LeadResponse)
def create_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_in: LeadCreate,
    auth_info: dict = Depends(deps.PermissionChecker("Lead", "Create")),
):
    db_lead = Lead(**lead_in.model_dump())
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    
    log_action(db, auth_info["user"].id, "Create", "Lead", db_lead.id, new_val=db_lead.name)
    return db_lead

@router.get("/", response_model=List[LeadResponse])
def get_leads(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
    auth_info: dict = Depends(deps.PermissionChecker("Lead", "View")),
):
    query = db.query(Lead)
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    
    if scope == "Own":
        query = query.filter(Lead.assigned_employee_id == curr_user.id)
    elif scope in ["Team", "Company"]:
        # Simplified: all leads in the same company
        query = query.join(Employee, Lead.assigned_employee_id == Employee.id).filter(Employee.company_id == curr_user.company_id)
        
    if search:
        query = query.filter(Lead.name.contains(search) | Lead.company.contains(search))
    if status:
        query = query.filter(Lead.status == status)
        
    return query.order_by(Lead.id.desc()).offset(skip).limit(limit).all()

@router.put("/{lead_id}", response_model=LeadResponse)
def update_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    lead_in: LeadUpdate,
    auth_info: dict = Depends(deps.PermissionChecker("Lead", "Edit")),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    # Enforce valid transitions if status is updated manually
    if lead_in.status and lead_in.status not in ["New", "Contacted", "Closed"]:
        if lead_in.status in ["Qualified", "Disqualified"]:
            raise HTTPException(status_code=400, detail="Use specific endpoints for qualification/disqualification.")

    update_data = lead_in.model_dump(exclude_unset=True)
    old_assigned = lead.assigned_employee_id
    for field, value in update_data.items():
        setattr(lead, field, value)
        
    db.commit()
    db.refresh(lead)
    
    # Audit Reassignment
    if "assigned_employee_id" in update_data and update_data["assigned_employee_id"] != old_assigned:
        log_action(db, auth_info["user"].id, "Reassign", "Lead", lead.id, old_val=str(old_assigned), new_val=str(lead.assigned_employee_id))
    else:
        log_action(db, auth_info["user"].id, "Edit", "Lead", lead.id)
        
    return lead

@router.post("/{lead_id}/qualify", response_model=LeadResponse)
def qualify_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    qualify_in: LeadQualify,
    auth_info: dict = Depends(deps.PermissionChecker("Lead", "Qualify Lead")),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.status in ["Qualified", "Closed", "Disqualified"]:
        raise HTTPException(status_code=400, detail=f"Cannot qualify a lead with status '{lead.status}'.")

    try:
        # Atomic Transaction
        lead.status = "Qualified"
        
        # Create Opportunity
        opp = Opportunity(
            name=f"{lead.company or lead.name} - Opportunity",
            lead_id=lead.id,
            expected_value=qualify_in.expected_value,
            probability=qualify_in.probability,
            assigned_employee_id=lead.assigned_employee_id,
            stage="Opportunity"
        )
        db.add(opp)
        db.commit()
        db.refresh(lead)
        db.refresh(opp)
        
        log_action(db, auth_info["user"].id, "Qualify", "Lead", lead.id, new_val="Qualified")
        log_action(db, auth_info["user"].id, "Create", "Opportunity", opp.id, new_val=opp.name)
        return lead
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Transaction failed")

@router.post("/{lead_id}/disqualify", response_model=LeadResponse)
def disqualify_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    disqualify_in: LeadDisqualify,
    auth_info: dict = Depends(deps.PermissionChecker("Lead", "Edit")),
):
    if not disqualify_in.reason or not disqualify_in.reason.strip():
        raise HTTPException(status_code=400, detail="Disqualification reason is required.")
        
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.status in ["Qualified", "Closed", "Disqualified"]:
        raise HTTPException(status_code=400, detail=f"Cannot disqualify a lead with status '{lead.status}'.")

    lead.status = "Disqualified"
    lead.disqualified_reason = disqualify_in.reason
    db.commit()
    db.refresh(lead)
    
    log_action(db, auth_info["user"].id, "Disqualify", "Lead", lead.id, new_val=lead.disqualified_reason)
    return lead
