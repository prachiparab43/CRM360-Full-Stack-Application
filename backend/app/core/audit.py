"""CRM360 Audit Logging Helper.

Adds audit log entries to the caller's database session without committing,
guaranteeing atomicity between entity state mutations and their audit trails.
Captures JSON old/new values and request context (IP, user-agent).
"""
import json
from typing import Optional, Any
from fastapi import Request
from sqlalchemy.orm import Session
from app.models.domain import AuditLog


def log_action(
    db: Session,
    user_id: Optional[int],
    action: str,
    module: str,
    record_id: Optional[int] = None,
    old_val: Optional[Any] = None,
    new_val: Optional[Any] = None,
    request: Optional[Request] = None,
    request_info: Optional[str] = None,
) -> AuditLog:
    """
    Creates an AuditLog and adds it to the active db session WITHOUT committing.
    Serializes dictionaries/lists into JSON strings.
    Extracts IP and user-agent from Request when available.
    """
    old_str = json.dumps(old_val, default=str) if isinstance(old_val, (dict, list)) else (str(old_val) if old_val is not None else None)
    new_str = json.dumps(new_val, default=str) if isinstance(new_val, (dict, list)) else (str(new_val) if new_val is not None else None)

    if request is not None:
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        req_dict = {"ip": client_ip, "user_agent": user_agent}
        req_info_str = json.dumps(req_dict)
    else:
        req_info_str = request_info

    log = AuditLog(
        user_id=user_id,
        action=action,
        module=module,
        record_id=record_id,
        old_value=old_str,
        new_value=new_str,
        request_info=req_info_str
    )
    db.add(log)
    return log
