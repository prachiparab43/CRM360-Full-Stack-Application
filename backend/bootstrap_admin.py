#!/usr/bin/env python3
"""
CRM360 - Secure Bootstrap Administrator Utility

Creates or verifies the initial System Administrator account in SQL Server.
Security Guarantees:
1. Password is entered securely via masked getpass prompt, never committed to git.
2. Checks for existing administrator to prevent duplicate accounts.
3. Assigns the seeded System Administrator role with All data scope and all catalog permissions.
4. Ensures status is 'Active' and company association is established.
5. Records creation in the Audit Log table.
6. Does NOT reset or truncate database tables.
"""

import os
import sys
import argparse
import getpass
from typing import Optional

# Ensure application modules can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.domain import Role, RolePermission, Employee, Company, AuditLog
from app.core.security import get_password_hash, validate_password_policy
from app.core.permissions import get_all_catalog_permissions
from app.core.audit import log_action

def get_or_create_system_role(db) -> Role:
    """Finds or seeds the System Administrator role with all catalog permissions at scope 'All'."""
    admin_role = db.query(Role).filter(Role.is_system == True).first()
    if not admin_role:
        admin_role = db.query(Role).filter(Role.name == "System Administrator").first()

    if not admin_role:
        print("[*] Creating System Administrator role...")
        admin_role = Role(
            name="System Administrator",
            description="Full system-wide administrative access to all CRM360 modules.",
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

    # Ensure all permissions from catalog exist with 'All' scope
    catalog_perms = get_all_catalog_permissions()
    existing_perms = {
        (p.module, p.action): p
        for p in db.query(RolePermission).filter(RolePermission.role_id == admin_role.id).all()
    }
    
    added_perms = 0
    for cp in catalog_perms:
        key = (cp["module"], cp["action"])
        if key not in existing_perms:
            db.add(RolePermission(
                role_id=admin_role.id,
                module=cp["module"],
                action=cp["action"],
                data_scope="All" if cp["data_scope"] != "Own" else "Own"
            ))
            added_perms += 1
    
    if added_perms > 0:
        db.commit()
        print(f"[*] Seeded {added_perms} catalog permissions into role '{admin_role.name}'.")

    return admin_role

def get_or_create_admin_company(db, company_name: str = "CRM360 Internal") -> Company:
    """Finds or creates an organizational workspace for the administrator."""
    company = db.query(Company).filter(Company.name == company_name).first()
    if not company:
        # Fall back to first existing company if available
        first_comp = db.query(Company).first()
        if first_comp:
            return first_comp
        print(f"[*] Creating administrative company: '{company_name}'...")
        company = Company(
            name=company_name,
            email="admin@crm360.local",
            phone="+1 (555) 000-0000",
            address="CRM360 Headquarters",
            status="Active"
        )
        db.add(company)
        db.commit()
        db.refresh(company)
    return company

def bootstrap_admin(
    name: str,
    email: str,
    password: Optional[str] = None,
    company_name: str = "CRM360 Internal",
    interactive: bool = True
) -> bool:
    clean_email = email.lower().strip()
    clean_name = name.strip()

    if not clean_email or "@" not in clean_email:
        print(f"[ERROR] Invalid email address: '{email}'")
        return False

    db = SessionLocal()
    try:
        # 1. Check if user already exists
        existing_user = db.query(Employee).filter(Employee.email == clean_email).first()
        if existing_user:
            admin_role = get_or_create_system_role(db)
            if existing_user.role_id == admin_role.id and existing_user.status == "Active":
                print(f"\n[INFO] Administrator account already exists and is active:")
                print(f"       Name:  {existing_user.name}")
                print(f"       Email: {existing_user.email}")
                print(f"       Role:  {admin_role.name} (ID: {admin_role.id})")
                print(f"       Status: {existing_user.status}")
                print("No duplicate account created.")
                return True
            else:
                print(f"[WARNING] An account with email '{clean_email}' already exists (ID: {existing_user.id}, Status: {existing_user.status}).")
                if interactive:
                    confirm = input("Would you like to upgrade this account to active System Administrator? (y/N): ").strip().lower()
                    if confirm != 'y':
                        print("[ABORTED] Operation cancelled by user.")
                        return False
                    existing_user.role_id = admin_role.id
                    existing_user.status = "Active"
                    if password:
                        validate_password_policy(password)
                        existing_user.password_hash = get_password_hash(password)
                    db.commit()
                    log_action(
                        db=db,
                        user_id=existing_user.id,
                        action="Upgrade Administrator",
                        module="Auth",
                        record_id=existing_user.id,
                        new_val={"email": existing_user.email, "role": "System Administrator", "status": "Active"}
                    )
                    db.commit()
                    print(f"[SUCCESS] User '{existing_user.email}' upgraded to active System Administrator.")
                    return True
                else:
                    print("[ERROR] Cannot create duplicate account. Aborting.")
                    return False

        # 2. Collect / Validate Password securely
        if not password:
            while True:
                p1 = getpass.getpass("Enter System Administrator password: ")
                if not p1:
                    print("[ERROR] Password cannot be empty.")
                    continue
                p2 = getpass.getpass("Confirm password: ")
                if p1 != p2:
                    print("[ERROR] Passwords do not match. Please try again.")
                    continue
                try:
                    validate_password_policy(p1)
                    password = p1
                    break
                except Exception as ex:
                    print(f"[ERROR] {ex}")
        else:
            validate_password_policy(password)

        # 3. Locate or seed System Administrator role and internal company
        admin_role = get_or_create_system_role(db)
        company = get_or_create_admin_company(db, company_name)

        # 4. Create new Administrator employee record
        new_admin = Employee(
            name=clean_name,
            email=clean_email,
            department="Executive / IT",
            designation="System Administrator",
            role_id=admin_role.id,
            company_id=company.id,
            password_hash=get_password_hash(password),
            status="Active",
            auth_provider="local"
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)

        # 5. Record creation in Audit Log
        log_action(
            db=db,
            user_id=new_admin.id,
            action="Bootstrap Administrator",
            module="Auth",
            record_id=new_admin.id,
            new_val={
                "name": new_admin.name,
                "email": new_admin.email,
                "role": admin_role.name,
                "role_id": admin_role.id,
                "data_scope": "All",
                "status": "Active",
                "company": company.name
            }
        )
        db.commit()

        print("\n" + "=" * 64)
        print(" [SUCCESS] CRM360 System Administrator Account Created")
        print("=" * 64)
        print(f" Full Name:   {new_admin.name}")
        print(f" Work Email:  {new_admin.email}")
        print(f" Role:        {admin_role.name} (Scope: All)")
        print(f" Status:      {new_admin.status}")
        print(f" Company:     {company.name} (ID: {company.id})")
        print(f" Audit Log:   Recorded (Action: 'Bootstrap Administrator')")
        print("=" * 64)
        print("You can now sign in at http://localhost:5173/ with these credentials.\n")
        return True

    except Exception as e:
        db.rollback()
        print(f"\n[FATAL ERROR] Failed to bootstrap administrator: {e}")
        return False
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="CRM360 Secure Administrator Bootstrap CLI")
    parser.add_argument("--name", default="System Administrator", help="Full name for the administrator")
    parser.add_argument("--email", help="Work email address for the administrator")
    parser.add_argument("--password", help="Password (optional; if omitted, you will be prompted securely without echo)")
    parser.add_argument("--company", default="CRM360 Internal", help="Company workspace name")

    args = parser.parse_args()

    email = args.email
    name = args.name

    if not email:
        print("\n=== CRM360 Administrator Bootstrap Wizard ===")
        name_input = input(f"Enter Administrator Full Name [{name}]: ").strip()
        if name_input:
            name = name_input
        while not email:
            email_input = input("Enter Administrator Work Email: ").strip()
            if email_input and "@" in email_input:
                email = email_input
            else:
                print("Please enter a valid work email address.")

    success = bootstrap_admin(
        name=name,
        email=email,
        password=args.password,
        company_name=args.company,
        interactive=args.password is None
    )

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
