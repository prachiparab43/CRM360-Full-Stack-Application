from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.models.domain import Company, Employee
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.core.audit import log_action

router = APIRouter()

@router.post("/", response_model=CompanyResponse)
def create_company(
    *,
    db: Session = Depends(deps.get_db),
    company_in: CompanyCreate,
    auth_info: dict = Depends(deps.PermissionChecker("Company", "Create")),
):
    # Check duplicate
    if db.query(Company).filter(Company.name == company_in.name).first():
        raise HTTPException(status_code=400, detail="Company with this name already exists.")
        
    db_company = Company(**company_in.model_dump())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    
    log_action(db, auth_info["user"].id, "Create", "Company", db_company.id, new_val=db_company.name)
    return db_company

@router.get("/", response_model=List[CompanyResponse])
def get_companies(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
    auth_info: dict = Depends(deps.PermissionChecker("Company", "View")),
):
    query = db.query(Company)
    scope = auth_info["scope"]
    
    if scope == "Own" or scope == "Team" or scope == "Company":
        query = query.filter(Company.id == auth_info["user"].company_id)
        
    if search:
        query = query.filter(Company.name.contains(search))
    if status:
        query = query.filter(Company.status == status)
        
    return query.order_by(Company.name).offset(skip).limit(limit).all()

@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    *,
    db: Session = Depends(deps.get_db),
    company_id: int,
    company_in: CompanyUpdate,
    auth_info: dict = Depends(deps.PermissionChecker("Company", "Edit")),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    # Enforce scope
    scope = auth_info["scope"]
    if scope in ["Own", "Team", "Company"] and company.id != auth_info["user"].company_id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this company")

    update_data = company_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
        
    db.commit()
    db.refresh(company)
    log_action(db, auth_info["user"].id, "Edit", "Company", company.id)
    return company
