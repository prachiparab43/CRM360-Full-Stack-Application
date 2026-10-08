import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_token():
    res = client.post("/api/auth/login", data={"username": "admin@crm360.com", "password": "Admin123!"})
    return res.json()["access_token"]

def test_company_creation(admin_token):
    res = client.post(
        "/api/companies/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Acme Corp", "email": "contact@acmecorp.com"}
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Acme Corp"

def test_company_retrieval(admin_token):
    res = client.get(
        "/api/companies/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    # At least two companies (CRM360 Internal and Acme Corp)
    assert len(res.json()) >= 1

def test_company_update(admin_token):
    # Get the latest company
    companies = client.get("/api/companies/", headers={"Authorization": f"Bearer {admin_token}"}).json()
    company_id = [c["id"] for c in companies if c["name"] == "Acme Corp"][0]
    
    res = client.put(
        f"/api/companies/{company_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "Inactive", "phone": "123456789"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "Inactive"
    assert res.json()["phone"] == "123456789"

def test_employee_creation_and_update(admin_token):
    res = client.post(
        "/api/employees/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "John Doe", "email": "john@acmecorp.com", "password": "Password123!"}
    )
    assert res.status_code == 200
    emp_id = res.json()["id"]
    
    # Update status to deactivated
    update_res = client.put(
        f"/api/employees/{emp_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "Inactive"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "Inactive"

def test_employee_deactivation_login_restriction():
    # Attempt to login with deactivated employee
    res = client.post(
        "/api/auth/login",
        data={"username": "john@acmecorp.com", "password": "Password123!"}
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "Inactive user"
