import fs from 'fs';
let tracking = fs.readFileSync('backend/app/api/endpoints/tracking.py', 'utf8');
tracking = tracking.replace(
    /def get_visits\([\s\S]*?return query\.order_by\(CustomerVisit\.id\.desc\(\)\)\.all\(\)/,
    `def get_visits(
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Visit", "View"))
):
    query = apply_scope(db.query(CustomerVisit), CustomerVisit, auth_info)
    return query.order_by(CustomerVisit.id.desc()).all()`
);
fs.writeFileSync('backend/app/api/endpoints/tracking.py', tracking);
console.log('Tracking fully patched');
