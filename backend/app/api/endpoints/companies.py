import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app.api import deps
from app.core.scope import apply_scope
from app.models.domain import Company, Employee
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.core.audit import log_action
from app.core.pagination import paginate_query

router = APIRouter()

ALLOWED_COMPANY_SORT = ["id", "name", "status", "phone", "email", "created_date"]

@router.post("/", response_model=CompanyResponse)
def create_company(
    *,
    db: Session = Depends(deps.get_db),
    company_in: CompanyCreate,
    request: Request,
    auth_info: dict = Depends(deps.PermissionChecker("Company", "Create")),
):
    if db.query(Company).filter(Company.name == company_in.name).first():
        raise HTTPException(status_code=400, detail="Company with this name already exists.")
        
    db_company = Company(**company_in.model_dump())
    db.add(db_company)
    db.flush()
    
    log_action(
        db,
        auth_info["user"].id,
        "Create",
        "Company",
        db_company.id,
        new_val={"name": db_company.name, "email": db_company.email},
        request=request
    )
    db.commit()
    db.refresh(db_company)
    return db_company

@router.get("/")
def get_companies(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: Optional[str] = "name",
    sort_dir: Optional[str] = "asc",
    paginate: bool = True,
    raw: bool = False,
    auth_info: dict = Depends(deps.PermissionChecker("Company", "View")),
):
    query = apply_scope(db.query(Company), Company, auth_info, db)
        
    if search:
        query = query.filter(Company.name.contains(search))
    if status:
        query = query.filter(Company.status == status)
        
    return paginate_query(
        query=query,
        model=Company,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
        allowed_sort_fields=ALLOWED_COMPANY_SORT,
        default_sort_field="name",
        default_sort_dir="asc",
        paginate=paginate,
        raw=raw,
    )

@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: int,
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Company", "View")),
):
    company = apply_scope(db.query(Company).filter(Company.id == company_id), Company, auth_info, db).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found or unauthorized")
    return company

@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    *,
    db: Session = Depends(deps.get_db),
    company_id: int,
    company_in: CompanyUpdate,
    request: Request,
    auth_info: dict = Depends(deps.PermissionChecker("Company", "Edit")),
):
    company = apply_scope(db.query(Company).filter(Company.id == company_id), Company, auth_info, db).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found or unauthorized")

    update_data = company_in.model_dump(exclude_unset=True)
    old_vals = {}
    new_vals = {}
    for field, value in update_data.items():
        curr_val = getattr(company, field)
        if curr_val != value:
            old_vals[field] = curr_val
            new_vals[field] = value
            setattr(company, field, value)
        
    log_action(
        db,
        auth_info["user"].id,
        "Edit",
        "Company",
        company.id,
        old_val=old_vals,
        new_val=new_vals,
        request=request
    )
    db.commit()
    db.refresh(company)
    return company
