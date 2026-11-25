import pytest
from fastapi.testclient import TestClient
from app.models.domain import Role, RolePermission, Employee, Company, AuditLog
from app.core.security import get_password_hash
from app.core.permissions import get_all_catalog_permissions

def _ensure_company(db_session):
    company = db_session.query(Company).first()
    if not company:
        company = Company(name="CRM360 Internal Test", email="test@crm360.local")
        db_session.add(company)
        db_session.commit()
        db_session.refresh(company)
    return company

def test_admin_creation_by_authorized_admin(client: TestClient, admin_token: str, db_session):
    """An authorized System Administrator can create another System Administrator via /api/employees/."""
    # 1. Locate System Administrator role and Company
    admin_role = db_session.query(Role).filter(Role.name == "System Administrator").first()
    assert admin_role is not None

    company = _ensure_company(db_session)

    new_admin_email = "new_sys_admin@crm360.com"
    # Ensure cleanup if exists
    existing = db_session.query(Employee).filter(Employee.email == new_admin_email).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    # 2. Create the admin user via protected endpoint
    res = client.post(
        "/api/employees/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Second System Administrator",
            "email": new_admin_email,
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "role_id": admin_role.id,
            "company_id": company.id,
            "status": "Active",
            "department": "IT",
            "designation": "System Administrator"
        }
    )
    assert res.status_code == 200, res.text
    created_data = res.json()
    assert created_data["email"] == new_admin_email
    assert created_data["status"] == "Active"
    assert created_data["role_id"] == admin_role.id
    new_admin_id = created_data["id"]

    # 3. Verify Login of New Administrator
    login_res = client.post(
        "/api/auth/login",
        data={"username": new_admin_email, "password": "SecurePassword123!"}
    )
    assert login_res.status_code == 200, login_res.text
    login_data = login_res.json()
    assert login_data["status"] == "Active"
    new_token = login_data["access_token"]

    # 4. Verify /api/auth/me loads all catalog permissions from database
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {new_token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["status"] == "Active"
    assert me_data["role_name"] == "System Administrator"
    assert len(me_data["permissions"]) >= 100
    # Check that permissions have scope 'All'
    all_scoped = [p for p in me_data["permissions"] if p["scope"] == "All"]
    assert len(all_scoped) >= 90

    # 5. Verify Duplicate Email is Blocked
    dup_res = client.post(
        "/api/employees/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Duplicate Admin",
            "email": new_admin_email,
            "password": "SecurePassword123!",
            "role_id": admin_role.id
        }
    )
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 6. Verify Administrator Creation is Recorded in Audit Log
    db_session.rollback()
    log = db_session.query(AuditLog).filter(
        AuditLog.record_id == new_admin_id,
        AuditLog.module == "Employee"
    ).first()
    assert log is not None
    assert "Create" in log.action

def test_unauthorized_user_cannot_create_administrator(client: TestClient, db_session):
    """A standard user or manager cannot escalate privileges or create a System Administrator."""
    company = _ensure_company(db_session)

    # 1. Create a limited role with only Employee:View and Employee:Create (scope Own)
    limited_role = Role(name="Limited HR", description="HR without admin assignment", status="Active", is_system=False)
    db_session.add(limited_role)
    db_session.commit()
    db_session.refresh(limited_role)

    db_session.add(RolePermission(role_id=limited_role.id, module="Employee", action="View", data_scope="Company"))
    db_session.add(RolePermission(role_id=limited_role.id, module="Employee", action="Create", data_scope="Company"))
    db_session.commit()

    hr_user = Employee(
        name="HR Staff",
        email="hr_staff@crm360.com",
        password_hash=get_password_hash("Password123!"),
        role_id=limited_role.id,
        company_id=company.id,
        status="Active"
    )
    db_session.add(hr_user)
    db_session.commit()

    # 2. Login as HR staff
    login_res = client.post("/api/auth/login", data={"username": "hr_staff@crm360.com", "password": "Password123!"})
    hr_token = login_res.json()["access_token"]

    admin_role = db_session.query(Role).filter(Role.name == "System Administrator").first()

    # 3. Attempt to create a System Administrator account (must fail with 403 Forbidden)
    escalate_res = client.post(
        "/api/employees/",
        headers={"Authorization": f"Bearer {hr_token}"},
        json={
            "name": "Illegitimate Admin",
            "email": "ill_admin@crm360.com",
            "password": "Password123!",
            "role_id": admin_role.id,
            "company_id": company.id
        }
    )
    assert escalate_res.status_code == 403
    assert "Role Assign permission required" in escalate_res.json()["detail"] or "Cannot assign a role" in escalate_res.json()["detail"]

def test_public_registration_cannot_register_system_admin(client: TestClient):
    """Public registration always quarantines new users with Pending_Approval and role_id=None."""
    reg_email = "self_register_hacker@crm360.com"
    res = client.post(
        "/api/auth/register",
        json={
            "name": "Self Register Hacker",
            "email": reg_email,
            "password": "SecretPassword123!",
            "confirm_password": "SecretPassword123!"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "Pending_Approval"

    # Login attempt must be blocked with 403
    login_res = client.post("/api/auth/login", data={"username": reg_email, "password": "SecretPassword123!"})
    assert login_res.status_code == 403
    assert "pending administrator approval" in login_res.json()["detail"]

def test_password_reset_and_status_toggle(client: TestClient, admin_token: str, db_session):
    """Test dedicated password reset and activate/deactivate endpoints."""
    company = _ensure_company(db_session)

    # Find or create a test employee
    emp = db_session.query(Employee).filter(Employee.email == "test_user_toggle@crm360.com").first()
    if not emp:
        emp = Employee(
            name="Toggle Employee",
            email="test_user_toggle@crm360.com",
            password_hash=get_password_hash("OldPassword123!"),
            company_id=company.id,
            status="Active"
        )
        db_session.add(emp)
        db_session.commit()
        db_session.refresh(emp)

    # 1. Reset Password
    reset_res = client.post(
        f"/api/employees/{emp.id}/reset-password",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"password": "NewSecretPassword123!", "confirm_password": "NewSecretPassword123!"}
    )
    assert reset_res.status_code == 200
    assert "reset successfully" in reset_res.json()["message"]

    # Verify login with new password
    login_res = client.post("/api/auth/login", data={"username": emp.email, "password": "NewSecretPassword123!"})
    assert login_res.status_code == 200

    # 2. Deactivate
    deact_res = client.post(
        f"/api/employees/{emp.id}/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert deact_res.status_code == 200
    assert deact_res.json()["status"] == "Inactive"

    # Verify login blocked while Inactive
    blocked_login = client.post("/api/auth/login", data={"username": emp.email, "password": "NewSecretPassword123!"})
    assert blocked_login.status_code == 403

    # 3. Activate
    act_res = client.post(
        f"/api/employees/{emp.id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert act_res.status_code == 200
    assert act_res.json()["status"] == "Active"
