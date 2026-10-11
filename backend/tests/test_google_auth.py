import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from tests.conftest import TestingSessionLocal
from app.models.domain import Employee, Role
from app.core import security

client = TestClient(app)

def test_google_auth_invalid_token():
    """Verify that an invalid or tampered Google token returns 401 Unauthorized."""
    response = client.post(
        "/api/auth/google",
        json={"id_token": "invalid_tampered_token_xyz"}
    )
    assert response.status_code == 401
    assert "Invalid or expired Google token" in response.json().get("detail", "")

def test_google_auth_new_user_quarantined():
    """
    Verify that a new Google user is created in quarantine:
    - Status is Pending_Approval
    - company_id is None
    - role_id is None
    - No JWT access token is issued
    """
    mock_payload = {
        "sub": "google-uid-1001",
        "email": "freshuser@example.com",
        "name": "Fresh Onboarding User"
    }
    
    with patch("app.api.endpoints.auth.verify_google_id_token", return_value=mock_payload):
        response = client.post(
            "/api/auth/google",
            json={"id_token": "valid_mock_google_id_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Pending_Approval"
        assert data.get("access_token") is None
        assert "pending administrator approval" in data["message"].lower()

        # Check DB directly in CRM360_Test
        db = TestingSessionLocal()
        created_user = db.query(Employee).filter(Employee.email == "freshuser@example.com").first()
        assert created_user is not None
        assert created_user.status == "Pending_Approval"
        assert created_user.company_id is None
        assert created_user.role_id is None
        assert created_user.password_hash is None
        assert created_user.google_sub == "google-uid-1001"
        assert created_user.auth_provider == "google"
        db.close()

def test_pending_user_cannot_access_protected_endpoints():
    """
    Verify that a pending/inactive user cannot access protected CRM endpoints,
    even if an attacker somehow forged a token for their user ID.
    """
    db = TestingSessionLocal()
    pending_user = db.query(Employee).filter(Employee.status == "Pending_Approval").first()
    assert pending_user is not None
    
    # Generate a JWT for this pending user ID
    token = security.create_access_token(pending_user.id)
    db.close()

    # Attempt to access protected /api/auth/me
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    # deps.get_current_active_user checks current_user.status == "Active"
    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive user"

def test_google_auth_account_conflict_rejection():
    """
    Verify that a Google login cannot hijack or auto-merge into an existing password account.
    Attempting Google login for admin@crm360.com (which has a password_hash) returns 409 Conflict.
    """
    mock_payload = {
        "sub": "google-uid-hijack-attempt",
        "email": "admin@crm360.com",
        "name": "Admin Impersonator"
    }

    with patch("app.api.endpoints.auth.verify_google_id_token", return_value=mock_payload):
        response = client.post(
            "/api/auth/google",
            json={"id_token": "valid_mock_google_id_token"}
        )
        assert response.status_code == 409
        assert "already exists with password login" in response.json()["detail"]

def test_google_auth_active_user_success():
    """
    Verify that once an administrator approves a Google user and sets status to Active,
    they can log in via Google and receive a valid CRM360 JWT token.
    """
    db = TestingSessionLocal()
    user = db.query(Employee).filter(Employee.email == "freshuser@example.com").first()
    admin_role = db.query(Role).filter(Role.name == "System Administrator").first()
    user.status = "Active"
    user.role_id = admin_role.id
    db.commit()
    db.close()

    mock_payload = {
        "sub": "google-uid-1001",
        "email": "freshuser@example.com",
        "name": "Fresh Onboarding User"
    }

    with patch("app.api.endpoints.auth.verify_google_id_token", return_value=mock_payload):
        response = client.post(
            "/api/auth/google",
            json={"id_token": "valid_mock_google_id_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Active"
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verify access token works on protected endpoints
        token = data["access_token"]
        me_res = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "freshuser@example.com"

def test_google_auth_returning_user_sub_lookup():
    """
    Verify returning Google user is identified directly by google_sub,
    even if email remains unchanged.
    """
    mock_payload = {
        "sub": "google-uid-1001",
        "email": "freshuser@example.com",
        "name": "Fresh Onboarding User"
    }

    with patch("app.api.endpoints.auth.verify_google_id_token", return_value=mock_payload):
        response = client.post(
            "/api/auth/google",
            json={"id_token": "valid_mock_google_id_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Active"
        assert "access_token" in data
        assert data["user"]["email"] == "freshuser@example.com"
