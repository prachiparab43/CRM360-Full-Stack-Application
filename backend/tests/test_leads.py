import pytest
from fastapi.testclient import TestClient
from main import app
from tests.conftest import TestingSessionLocal as SessionLocal
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

def _create_lead(admin_token):
    res = client.post(
        "/api/leads/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "New Potential Client", "company": "Tech Solutions"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "New"
    return res.json()["id"]

def test_lead_creation(admin_token, setup_lead_permissions):
    lead_id = _create_lead(admin_token)
    assert lead_id is not None

def test_lead_retrieval(admin_token):
    res = client.get(
        "/api/leads/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    assert len(res.json()) >= 1

def test_lead_reassignment(admin_token):
    # First create a lead
    lead_id = _create_lead(admin_token)
    
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
    lead_id = _create_lead(admin_token)
    
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
    lead_id = _create_lead(admin_token)
    client.post(f"/api/leads/{lead_id}/qualify", headers={"Authorization": f"Bearer {admin_token}"}, json={})
    
    # Try again
    res2 = client.post(f"/api/leads/{lead_id}/qualify", headers={"Authorization": f"Bearer {admin_token}"}, json={})
    assert res2.status_code == 400
    assert "Cannot qualify" in res2.json()["detail"]

def test_lead_disqualification(admin_token):
    lead_id = _create_lead(admin_token)
    
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

def test_lead_conversion_success_and_traceability(admin_token):
    # 1. Create a lead
    res = client.post(
        "/api/leads/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Conversion Test Lead",
            "company": "Acme Ventures",
            "contact_name": "Alice Smith",
            "email": "alice@acmeventures.com",
            "phone": "+1 555-0199",
            "lead_source": "Conference",
            "requirement": "Enterprise CRM deployment"
        }
    )
    assert res.status_code == 200
    lead_id = res.json()["id"]

    # 2. Convert to Opportunity
    convert_res = client.post(
        f"/api/leads/{lead_id}/convert",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Acme Ventures - Enterprise Rollout",
            "expected_value": 75000.0,
            "probability": 25.0,
            "stage": "Opportunity",
            "notes": "Qualified via initial discovery call"
        }
    )
    assert convert_res.status_code == 200
    lead_data = convert_res.json()
    assert lead_data["status"] == "Qualified"
    assert lead_data["opportunity_id"] is not None
    assert lead_data["opportunity_name"] == "Acme Ventures - Enterprise Rollout"
    opp_id = lead_data["opportunity_id"]

    # 3. Verify Opportunity traceability
    opp_res = client.get(
        f"/api/opportunities/{opp_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert opp_res.status_code == 200
    opp_data = opp_res.json()
    assert opp_data["lead_id"] == lead_id
    assert opp_data["lead_name"] == "Conversion Test Lead"
    assert opp_data["lead_company"] == "Acme Ventures"
    assert opp_data["lead_source"] == "Conference"
    assert opp_data["expected_value"] == 75000.0

    # 4. Duplicate conversion attempt must fail
    dup_res = client.post(
        f"/api/leads/{lead_id}/convert",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Duplicate Deal"}
    )
    assert dup_res.status_code == 400
    assert "already been converted" in dup_res.json()["detail"]

def test_lead_conversion_disqualified_fails(admin_token):
    res = client.post(
        "/api/leads/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Disqualified Lead", "company": "NoGo Corp"}
    )
    lead_id = res.json()["id"]
    client.post(
        f"/api/leads/{lead_id}/disqualify",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"reason": "Not a fit"}
    )

    # Conversion should fail
    fail_res = client.post(
        f"/api/leads/{lead_id}/convert",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Invalid Deal"}
    )
    assert fail_res.status_code == 400
    assert "Cannot convert a disqualified lead" in fail_res.json()["detail"]


