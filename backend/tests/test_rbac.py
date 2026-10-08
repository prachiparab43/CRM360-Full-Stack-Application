import pytest
from fastapi.testclient import TestClient
from main import app
from app.db.session import SessionLocal
from app.models.domain import Employee, Role
from app.core.security import get_password_hash

client = TestClient(app)

def setup_test_data():
    db = SessionLocal()
    # Create an employee with no roles to test 403 Forbidden
    test_user = db.query(Employee).filter(Employee.email == "test_user@crm360.com").first()
    if not test_user:
        role = Role(name="Empty Role", description="No permissions")
        db.add(role)
        db.commit()
        db.refresh(role)
        
        test_user = Employee(
            name="Test User",
            email="test_user@crm360.com",
            role_id=role.id,
            password_hash=get_password_hash("TestUser123!"),
            status="Active"
        )
        db.add(test_user)
        db.commit()
    db.close()

@pytest.fixture(scope="module", autouse=True)
def run_setup():
    setup_test_data()
    yield

def get_admin_token():
    res = client.post("/api/auth/login", data={"username": "admin@crm360.com", "password": "Admin123!"})
    return res.json()["access_token"]

def get_test_user_token():
    res = client.post("/api/auth/login", data={"username": "test_user@crm360.com", "password": "TestUser123!"})
    return res.json()["access_token"]

def test_admin_can_create_role():
    token = get_admin_token()
    response = client.post(
        "/api/roles/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Sales Manager",
            "description": "Manages regional sales",
            "permissions": [
                {"module": "Lead", "action": "View", "data_scope": "Team"},
                {"module": "Lead", "action": "Create", "data_scope": "Team"}
            ]
        }
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Sales Manager"
    assert len(response.json()["permissions"]) == 2

def test_test_user_denied_create_role():
    token = get_test_user_token()
    response = client.post(
        "/api/roles/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Hacker Role",
            "permissions": []
        }
    )
    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]
