from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.models.domain import Opportunity, Customer, Employee, Lead
from app.schemas.opportunity import OpportunityCreate, OpportunityUpdate, OpportunityStageUpdate, OpportunityResponse
from app.core.audit import log_action

router = APIRouter()

@router.post("/", response_model=OpportunityResponse)
def create_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_in: OpportunityCreate,
    auth_info: dict = Depends(deps.PermissionChecker("Opportunity", "Create")),
):
    db_opp = Opportunity(**opp_in.model_dump())
    db.add(db_opp)
    db.commit()
    db.refresh(db_opp)
    
    log_action(db, auth_info["user"].id, "Create", "Opportunity", db_opp.id, new_val=db_opp.name)
    return db_opp

@router.get("/", response_model=List[OpportunityResponse])
def get_opportunities(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    stage: Optional[str] = None,
    auth_info: dict = Depends(deps.PermissionChecker("Opportunity", "View")),
):
    query = db.query(Opportunity)
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    
    if scope == "Own":
        query = query.filter(Opportunity.assigned_employee_id == curr_user.id)
    elif scope in ["Team", "Company"]:
        query = query.join(Employee, Opportunity.assigned_employee_id == Employee.id).filter(Employee.company_id == curr_user.company_id)
        
    if search:
        query = query.filter(Opportunity.name.contains(search))
    if stage:
        query = query.filter(Opportunity.stage == stage)
        
    return query.order_by(Opportunity.id.desc()).offset(skip).limit(limit).all()

@router.put("/{opp_id}", response_model=OpportunityResponse)
def update_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    opp_in: OpportunityUpdate,
    auth_info: dict = Depends(deps.PermissionChecker("Opportunity", "Edit")),
):
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    if opp.stage in ["Won", "Lost"]:
        raise HTTPException(status_code=400, detail="Cannot edit a Won or Lost opportunity.")

    update_data = opp_in.model_dump(exclude_unset=True)
    old_assigned = opp.assigned_employee_id
    
    for field, value in update_data.items():
        setattr(opp, field, value)
        
    db.commit()
    db.refresh(opp)
    
    if "assigned_employee_id" in update_data and update_data["assigned_employee_id"] != old_assigned:
        log_action(db, auth_info["user"].id, "Reassign", "Opportunity", opp.id, old_val=str(old_assigned), new_val=str(opp.assigned_employee_id))
    else:
        log_action(db, auth_info["user"].id, "Edit", "Opportunity", opp.id)
        
    return opp

@router.post("/{opp_id}/stage", response_model=OpportunityResponse)
def change_stage(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    stage_in: OpportunityStageUpdate,
    auth_info: dict = Depends(deps.PermissionChecker("Opportunity", "Change Stage")),
):
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    if opp.stage in ["Won", "Lost"]:
        raise HTTPException(status_code=400, detail="Cannot change stage of a Won or Lost opportunity.")

    VALID_TRANSITIONS = {
        "Opportunity": ["Proposal", "Lost", "Won"],
        "Proposal": ["Negotiation", "Lost", "Won"],
        "Negotiation": ["Won", "Lost"]
    }
    
    if stage_in.stage not in VALID_TRANSITIONS.get(opp.stage, []):
        raise HTTPException(status_code=400, detail=f"Invalid transition from {opp.stage} to {stage_in.stage}")

    if stage_in.stage == "Lost":
        if not stage_in.lost_reason or not stage_in.lost_reason.strip():
            raise HTTPException(status_code=400, detail="Lost Reason is required when marking opportunity as Lost.")
        opp.lost_reason = stage_in.lost_reason

    if stage_in.stage == "Won":
        try:
            customer_name = opp.name.replace(" - Opportunity", "")
            if opp.lead_id:
                lead = db.query(Lead).filter(Lead.id == opp.lead_id).first()
                if lead and lead.company:
                    customer_name = lead.company

            customer = db.query(Customer).filter(Customer.name == customer_name).first()
            if not customer:
                customer = Customer(
                    name=customer_name,
                    assigned_employee_id=opp.assigned_employee_id,
                    status="Active"
                )
                db.add(customer)
                db.flush()
            
            opp.customer_id = customer.id
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Transaction failed during customer creation")

    old_stage = opp.stage
    opp.stage = stage_in.stage
    db.commit()
    db.refresh(opp)

    log_action(db, auth_info["user"].id, "Change Stage", "Opportunity", opp.id, old_val=old_stage, new_val=opp.stage)
    return opp
