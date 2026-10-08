import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.db.session import SessionLocal
from app.models.domain import Role, RolePermission, Employee, Company
from app.core.security import get_password_hash

def init_db():
    db = SessionLocal()
    
    # Check if admin role exists
    admin_role = db.query(Role).filter(Role.name == "System Administrator").first()
    if not admin_role:
        admin_role = Role(name="System Administrator", description="Full system access")
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)
        
        # Add basic permissions
        modules = ["Company", "Employee", "Role", "Lead", "Opportunity", "Customer", "Contact"]
        for mod in modules:
            for action in ["Create", "View", "Edit", "Delete"]:
                db.add(RolePermission(role_id=admin_role.id, module=mod, action=action, data_scope="All"))
        db.commit()

    # Create company for admin
    company = db.query(Company).filter(Company.name == "CRM360 Internal").first()
    if not company:
        company = Company(name="CRM360 Internal", email="admin@crm360.local")
        db.add(company)
        db.commit()
        db.refresh(company)

    # Check if admin user exists
    admin_user = db.query(Employee).filter(Employee.email == "admin@crm360.local").first()
    if not admin_user:
        admin_user = Employee(
            name="System Admin",
            email="admin@crm360.local",
            department="IT",
            designation="Administrator",
            role_id=admin_role.id,
            company_id=company.id,
            password_hash=get_password_hash("Admin123!"),
            status="Active"
        )
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully: admin@crm360.local / Admin123!")
    else:
        print("Admin user already exists.")
    
    db.close()

if __name__ == "__main__":
    init_db()
