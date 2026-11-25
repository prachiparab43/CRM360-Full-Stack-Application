import os
import sys
import secrets
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.db.session import SessionLocal
from app.models.domain import Role, RolePermission, Employee, Company
from app.core.security import get_password_hash
from app.core.permissions import get_all_catalog_permissions

def init_db():
    db = SessionLocal()
    
    # 1. Locate or create the seeded system role (no hard-coded role names)
    admin_role = db.query(Role).filter(Role.is_system == True).first()
    if not admin_role:
        role_name = os.getenv("ADMIN_ROLE_NAME", "System Admin Role")
        admin_role = Role(
            name=role_name,
            description="Full system access",
            status="Active",
            is_system=True
        )
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)
    else:
        if admin_role.status != "Active":
            admin_role.status = "Active"
            db.commit()

    # 2. Seed the full catalog idempotently (re-running adds new permissions)
    catalog_perms = get_all_catalog_permissions()
    existing_perms = {
        (p.module, p.action): p
        for p in db.query(RolePermission).filter(RolePermission.role_id == admin_role.id).all()
    }
    
    added_count = 0
    for cp in catalog_perms:
        key = (cp["module"], cp["action"])
        if key not in existing_perms:
            db.add(RolePermission(
                role_id=admin_role.id,
                module=cp["module"],
                action=cp["action"],
                data_scope=cp["data_scope"]
            ))
            added_count += 1
            
    db.commit()
    if added_count > 0:
        print(f"Seeded {added_count} new permissions into system role {admin_role.id}.")

    # 3. Create company for admin if needed
    company = db.query(Company).filter(Company.name == "CRM360 Internal").first()
    if not company:
        company = Company(name="CRM360 Internal", email="admin@crm360.local")
        db.add(company)
        db.commit()
        db.refresh(company)

    # 4. Check if admin user exists
    admin_email = os.getenv("ADMIN_EMAIL", "admin@crm360.com")
    admin_password = os.getenv("ADMIN_PASSWORD")
    is_auto_generated = False
    if not admin_password:
        is_auto_generated = True
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
        if is_auto_generated:
            print(f"Password: {admin_password}")
    else:
        print("Admin user already exists.")
    
    db.close()

if __name__ == "__main__":
    init_db()
