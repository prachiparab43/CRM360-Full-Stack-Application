import pytest
from fastapi.testclient import TestClient
from main import app
from app.db.session import SessionLocal
from app.models.domain import Opportunity, RolePermission, Role

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_token():
    res = client.post("/api/auth/login", data={"username": "admin@crm360.com", "password": "Admin123!"})
    return res.json()["access_token"]

@pytest.fixture(scope="module")
def setup_lead_permissions():
    db = SessionLocal()
    role = db.query(Role).filter(Role.name == "System Administrator").first()
    # Add explicit Qualify Lead permission if it wasn't added
    perm = db.query(RolePermission).filter(RolePermission.role_id == role.id, RolePermission.action == "Qualify Lead").first()
    if not perm:
        db.add(RolePermission(role_id=role.id, module="Lead", action="Qualify Lead", data_scope="All"))
        db.commit()
    db.close()

def test_lead_creation(admin_token, setup_lead_permissions):
    res = client.post(
        "/api/leads/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "New Potential Client", "company": "Tech Solutions"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "New"
    return res.json()["id"]

def test_lead_retrieval(admin_token):
    res = client.get(
        "/api/leads/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    assert len(res.json()) >= 1

def test_lead_reassignment(admin_token):
    # First create a lead
    lead_id = test_lead_creation(admin_token, None)
    
    # Reassign (we just simulate assigning to an employee ID, let's use employee ID 1, the admin)
    res = client.put(
        f"/api/leads/{lead_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"assigned_employee_id": 1, "status": "Contacted"}
    )
    assert res.status_code == 200
    assert res.json()["assigned_employee_id"] == 1
    assert res.json()["status"] == "Contacted"

def test_lead_qualification(admin_token):
    lead_id = test_lead_creation(admin_token, None)
    
    # Qualify
    res = client.post(
        f"/api/leads/{lead_id}/qualify",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"expected_value": 50000}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "Qualified"
    
    # Verify Opportunity was created atomically
    db = SessionLocal()
    opp = db.query(Opportunity).filter(Opportunity.lead_id == lead_id).first()
    assert opp is not None
    assert opp.expected_value == 50000
    db.close()

def test_duplicate_qualification_prevention(admin_token):
    lead_id = test_lead_creation(admin_token, None)
    client.post(f"/api/leads/{lead_id}/qualify", headers={"Authorization": f"Bearer {admin_token}"}, json={})
    
    # Try again
    res2 = client.post(f"/api/leads/{lead_id}/qualify", headers={"Authorization": f"Bearer {admin_token}"}, json={})
    assert res2.status_code == 400
    assert "Cannot qualify" in res2.json()["detail"]

def test_lead_disqualification(admin_token):
    lead_id = test_lead_creation(admin_token, None)
    
    # Try without reason (should fail)
    res = client.post(f"/api/leads/{lead_id}/disqualify", headers={"Authorization": f"Bearer {admin_token}"}, json={"reason": ""})
    assert res.status_code == 400
    
    # Try with reason
    res = client.post(f"/api/leads/{lead_id}/disqualify", headers={"Authorization": f"Bearer {admin_token}"}, json={"reason": "Not interested"})
    assert res.status_code == 200
    assert res.json()["status"] == "Disqualified"
    assert res.json()["disqualified_reason"] == "Not interested"

def test_unauthorized_access():
    res = client.get("/api/leads/")
    assert res.status_code == 401 # No token

    # Note: RBAC 403 Forbidden is already covered generically in test_rbac.py
