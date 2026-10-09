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
    admin_email = os.getenv("ADMIN_EMAIL", "admin@crm360.com")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        print("Warning: ADMIN_PASSWORD environment variable not set. Using a securely generated random password.")
        import secrets
        admin_password = secrets.token_urlsafe(12)

    admin_user = db.query(Employee).filter(Employee.email == admin_email).first()
    if not admin_user:
        admin_user = Employee(
            name="System Admin",
            email=admin_email,
            department="IT",
            designation="Administrator",
            role_id=admin_role.id,
            company_id=company.id,
            password_hash=get_password_hash(admin_password),
            status="Active"
        )
        db.add(admin_user)
        db.commit()
        print(f"Admin user created successfully: {admin_email}")
        print(f"Password: {admin_password}")
    else:
        print("Admin user already exists.")
    
    db.close()

if __name__ == "__main__":
    init_db()
