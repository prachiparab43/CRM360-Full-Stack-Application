import fs from 'fs';
let content = fs.readFileSync('backend/app/api/endpoints/contacts.py', 'utf8');

content = content.replace('from app.api import deps', 'from app.api import deps\\nfrom app.api.endpoints.dashboard import apply_scope');
content = content.replace(
    'contact = db.query(Contact).filter(Contact.id == contact_id).first()',
    'contact = apply_scope(db.query(Contact).filter(Contact.id == contact_id), Contact, auth_info).first()'
);

fs.writeFileSync('backend/app/api/endpoints/contacts.py', content);
console.log('Contacts patched');
