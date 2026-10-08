from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import csv
import io
from datetime import date
from typing import Optional

from app.api import deps
from app.models.domain import Lead, Opportunity
from app.api.endpoints.dashboard import apply_scope
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

@router.get("/opportunities/export")
def export_opportunities(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    stage: Optional[str] = None,
    auth_info: dict = Depends(deps.PermissionChecker("Report", "Export"))
):
    query = apply_scope(db.query(Opportunity), Opportunity, auth_info)
    
    if stage:
        query = query.filter(Opportunity.stage == stage)
    if start_date:
        query = query.filter(Opportunity.expected_close_date >= start_date)
    if end_date:
        query = query.filter(Opportunity.expected_close_date <= end_date)
        
    opps = query.all()
    headers = ["ID", "Name", "Expected Value", "Stage", "Assigned Employee ID"]
    rows = [[o.id, o.name, o.expected_value, o.stage, o.assigned_employee_id] for o in opps]
    
    log_action(db, auth_info["user"].id, "Export", "Report", 0, new_val="opportunities_export.csv")
    return generate_csv_response("opportunities_export.csv", headers, rows)
