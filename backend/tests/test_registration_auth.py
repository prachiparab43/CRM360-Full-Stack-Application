import pytest
import uuid
from fastapi.testclient import TestClient
from main import app
from tests.conftest import TestingSessionLocal
from app.models.domain import Employee, Role, Company
from app.core import security

client = TestClient(app)

def test_registration_success():
    """Verify that a new user can register with email and password and enters Pending_Approval."""
    unique_email = f"reg_{uuid.uuid4().hex[:6]}@enterprise.com"
    payload = {
        "name": "Jane Developer",
        "email": unique_email,
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "phone": "+1-555-0199"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Pending_Approval"
    assert "pending administrator approval" in data["message"].lower()
    assert data["user"]["email"] == unique_email
    assert data["user"]["name"] == "Jane Developer"

    # Verify database state
    db = TestingSessionLocal()
    user = db.query(Employee).filter(Employee.email == unique_email).first()
    assert user is not None
    assert user.status == "Pending_Approval"
    assert user.company_id is None
    assert user.role_id is None
    assert user.password_hash is not None
    assert security.verify_password("SecurePassword123!", user.password_hash)
    db.close()

def test_registration_password_policy():
    """Verify that weak passwords are rejected during registration."""
    unique_email = f"reg_{uuid.uuid4().hex[:6]}@enterprise.com"
    # Too short (<8)
    res1 = client.post("/api/auth/register", json={
        "name": "Test User",
        "email": unique_email,
        "password": "sh1",
        "confirm_password": "sh1"
    })
    assert res1.status_code == 400
    assert "at least 8 characters" in res1.json()["detail"].lower()

    # No digits
    res2 = client.post("/api/auth/register", json={
        "name": "Test User",
        "email": unique_email,
        "password": "lettersonlyhere",
        "confirm_password": "lettersonlyhere"
    })
    assert res2.status_code == 400
    assert "both letters and numbers" in res2.json()["detail"].lower()

def test_registration_confirm_password_mismatch():
    """Verify that password mismatch is rejected."""
    unique_email = f"reg_{uuid.uuid4().hex[:6]}@enterprise.com"
    res = client.post("/api/auth/register", json={
        "name": "Test User",
        "email": unique_email,
        "password": "Password123",
        "confirm_password": "PasswordMismatch999"
    })
    assert res.status_code == 400
    assert "passwords do not match" in res.json()["detail"].lower()

def test_registration_duplicate_email():
    """Verify that duplicate email registration is rejected."""
    unique_email = f"reg_{uuid.uuid4().hex[:6]}@enterprise.com"
    payload = {
        "name": "First Register",
        "email": unique_email,
        "password": "Password123",
        "confirm_password": "Password123"
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 200

    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()

def test_pending_user_login_blocked():
    """Verify that a newly registered pending user cannot log in and gets 403."""
    unique_email = f"reg_{uuid.uuid4().hex[:6]}@enterprise.com"
    client.post("/api/auth/register", json={
        "name": "Pending Login User",
        "email": unique_email,
        "password": "Password123",
        "confirm_password": "Password123"
    })

    login_res = client.post("/api/auth/login", data={
        "username": unique_email,
        "password": "Password123"
    })
    assert login_res.status_code == 403
    assert "pending administrator approval" in login_res.json()["detail"].lower()

def test_admin_approves_user_and_user_can_login(admin_token):
    """
    Verify full lifecycle:
    1. User registers (status = Pending_Approval)
    2. Admin assigns Company and Role, sets status to Active
    3. User successfully logs in with password and receives JWT
    4. User can access authorized endpoints
    """
    unique_email = f"reg_{uuid.uuid4().hex[:6]}@enterprise.com"
    client.post("/api/auth/register", json={
        "name": "Approved User",
        "email": unique_email,
        "password": "Password123",
        "confirm_password": "Password123"
    })

    db = TestingSessionLocal()
    company = db.query(Company).first()
    if not company:
        company = Company(name="Acme Enterprise", email="contact@acme.com")
        db.add(company)
        db.commit()
        db.refresh(company)
    user = db.query(Employee).filter(Employee.email == unique_email).first()
    role = db.query(Role).first()
    user_id = user.id
    company_id = company.id
    role_id = role.id
    db.close()

    # Admin approves user
    approve_res = client.put(
        f"/api/employees/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "status": "Active",
            "company_id": company_id,
            "role_id": role_id
        }
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "Active"

    # Now user logs in
    login_res = client.post("/api/auth/login", data={
        "username": unique_email,
        "password": "Password123"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # User accesses /api/auth/me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == unique_email
    assert me_res.json()["status"] == "Active"
    assert me_res.json()["company_id"] == company_id
    assert me_res.json()["role_id"] == role_id

