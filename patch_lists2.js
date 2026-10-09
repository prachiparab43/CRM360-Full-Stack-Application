import fs from 'fs';
let content = fs.readFileSync('backend/app/api/endpoints/engagements.py', 'utf8');

content = content.replace(
    /def get_tasks\([\s\S]*?return query\.order_by\(Task\.due_date\)\.all\(\)/,
    `def get_tasks(
    db: Session = Depends(deps.get_db),
    overdue: bool = False,
    auth_info: dict = Depends(deps.PermissionChecker("Task", "View"))
):
    query = apply_scope(db.query(Task), Task, auth_info)
    if overdue:
        query = query.filter(Task.due_date < datetime.now().date(), Task.status.notin_(["Completed", "Cancelled"]))
    return query.order_by(Task.due_date).all()`
);

content = content.replace(
    /def get_meetings\([\s\S]*?return query\.order_by\(Meeting\.date\)\.all\(\)/,
    `def get_meetings(
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Meeting", "View"))
):
    query = apply_scope(db.query(Meeting), Meeting, auth_info)
    return query.order_by(Meeting.date).all()`
);

fs.writeFileSync('backend/app/api/endpoints/engagements.py', content);
console.log('Engagements lists fully patched');
