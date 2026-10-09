import fs from 'fs';
let content = fs.readFileSync('backend/app/api/endpoints/dashboard.py', 'utf8');

const newFunc = `from fastapi import HTTPException
from app.models.domain import Contact

def apply_scope(query, model, auth_info):
    scope = auth_info["scope"]
    curr_user = auth_info["user"]
    if scope == "All":
        return query
        
    emp_col = None
    if model == Contact:
        # Avoid duplicate join if Customer already joined
        if 'Customer' not in str(query):
            query = query.join(Customer, Contact.customer_id == Customer.id)
        emp_col = Customer.assigned_employee_id
    elif hasattr(model, 'assigned_employee_id'): 
        emp_col = model.assigned_employee_id
    elif hasattr(model, 'employee_id'): 
        emp_col = model.employee_id
    elif model == Employee: 
        emp_col = model.id
        
    if emp_col is None:
        raise HTTPException(status_code=403, detail=f"Cannot apply RBAC scope to model {model.__name__}")

    if scope == "Own":
        return query.filter(emp_col == curr_user.id)
    elif scope in ["Team", "Company"]:
        if model != Employee and 'Employee' not in str(query):
            query = query.join(Employee, emp_col == Employee.id)
        return query.filter(Employee.company_id == curr_user.company_id)
    
    raise HTTPException(status_code=403, detail="Invalid scope type")`;

content = content.replace(/def apply_scope\(query, model, auth_info\):[\s\S]*?return query\n/, newFunc + '\n');
fs.writeFileSync('backend/app/api/endpoints/dashboard.py', content);
console.log('Done');
