from sqlalchemy.orm import Session
from app.models.domain import AuditLog

def log_action(db: Session, user_id: int, action: str, module: str, record_id: int, old_val: str = None, new_val: str = None):
    log = AuditLog(
        user_id=user_id,
        action=action,
        module=module,
        record_id=record_id,
        old_value=old_val,
        new_value=new_val
    )
    db.add(log)
    db.commit()
