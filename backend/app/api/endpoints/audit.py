import csv
import io
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Any
from datetime import datetime

from app.api import deps
from app.models.domain import AuditLog, Employee
from app.schemas.audit import AuditLogResponse
from app.core.scope import apply_scope
from app.core.pagination import paginate_query

router = APIRouter()

ALLOWED_AUDIT_SORT_FIELDS = ["id", "timestamp", "module", "action", "user_id", "record_id"]

def _to_audit_response(log: AuditLog) -> AuditLogResponse:
    return AuditLogResponse(
        id=log.id,
        user_id=log.user_id,
        user_name=log.user.name if log.user else None,
        action=log.action,
        module=log.module,
        record_id=log.record_id,
        old_value=log.old_value,
        new_value=log.new_value,
        timestamp=log.timestamp,
        request_info=log.request_info,
    )

@router.get("/")
def get_audit_logs(
    db: Session = Depends(deps.get_db),
    user_id: Optional[int] = None,
    module: Optional[str] = None,
    action: Optional[str] = None,
    record_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = "timestamp",
    sort_dir: Optional[str] = "desc",
    paginate: bool = True,
    raw: bool = False,
    format: str = Query("json"),
    auth_info: dict = Depends(deps.PermissionChecker("AuditLog", "View")),
):
    query = db.query(AuditLog)
    query = apply_scope(query, AuditLog, auth_info, db)

    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if module:
        query = query.filter(AuditLog.module == module)
    if action:
        query = query.filter(AuditLog.action == action)
    if record_id is not None:
        query = query.filter(AuditLog.record_id == record_id)
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)

    if format == "csv":
        # CSV Export requires AuditLog: Export permission
        deps.PermissionChecker("AuditLog", "Export")(auth_info["user"], db)
        logs = query.order_by(AuditLog.timestamp.desc()).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Timestamp", "User ID", "User Name", "Module", "Action", "Record ID", "Old Value", "New Value", "Request Info"])
        for l in logs:
            writer.writerow([
                l.id,
                l.timestamp.isoformat() if l.timestamp else "",
                l.user_id,
                l.user.name if l.user else "",
                l.module,
                l.action,
                l.record_id,
                l.old_value,
                l.new_value,
                l.request_info
            ])
        output.seek(0)
        resp = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
        resp.headers["Content-Disposition"] = "attachment; filename=audit_logs.csv"
        return resp

    res = paginate_query(
        query=query,
        model=AuditLog,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
        allowed_sort_fields=ALLOWED_AUDIT_SORT_FIELDS,
        default_sort_field="timestamp",
        default_sort_dir="desc",
        paginate=paginate,
        raw=raw,
    )

    if isinstance(res, dict):
        return {
            "items": [_to_audit_response(l) for l in res["items"]],
            "total": res["total"],
            "skip": res["skip"],
            "limit": res["limit"],
        }
    return [_to_audit_response(l) for l in res]
