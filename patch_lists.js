import fs from 'fs';
let content = fs.readFileSync('backend/app/api/endpoints/engagements.py', 'utf8');

// Fix get_activities
content = content.replace(
    'return db.query(Activity).order_by(Activity.id.desc()).all()',
    'return apply_scope(db.query(Activity), Activity, auth_info).order_by(Activity.id.desc()).all()'
);

// Fix get_tasks
content = content.replace(
    'return query.order_by(Task.due_date.asc()).all()',
    'return apply_scope(query, Task, auth_info).order_by(Task.due_date.asc()).all()'
);

// Fix get_meetings
content = content.replace(
    'return query.order_by(Meeting.date.asc()).all()',
    'return apply_scope(query, Meeting, auth_info).order_by(Meeting.date.asc()).all()'
);

fs.writeFileSync('backend/app/api/endpoints/engagements.py', content);
console.log('Engagements patched');

let tracking = fs.readFileSync('backend/app/api/endpoints/tracking.py', 'utf8');
tracking = tracking.replace(
    'return db.query(CustomerVisit).order_by(CustomerVisit.visit_date.asc()).all()',
    'return apply_scope(db.query(CustomerVisit), CustomerVisit, auth_info).order_by(CustomerVisit.visit_date.asc()).all()'
);
if (!tracking.includes('apply_scope')) {
    tracking = tracking.replace('from app.api import deps', 'from app.api import deps\\nfrom app.api.endpoints.dashboard import apply_scope');
}
fs.writeFileSync('backend/app/api/endpoints/tracking.py', tracking);
console.log('Tracking patched');
