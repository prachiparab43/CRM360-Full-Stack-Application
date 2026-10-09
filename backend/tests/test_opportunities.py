import pytest
from fastapi.testclient import TestClient
from main import app
from tests.conftest import TestingSessionLocal as SessionLocal
from app.models.domain import RolePermission, Role, Customer

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_token():
    res = client.post("/api/auth/login", data={"username": "admin@crm360.com", "password": "Admin123!"})
    return res.json()["access_token"]

@pytest.fixture(scope="module")
def setup_opp_permissions():
    db = SessionLocal()
    role = db.query(Role).filter(Role.name == "System Administrator").first()
    perms = [
        RolePermission(role_id=role.id, module="Opportunity", action="Change Stage", data_scope="All"),
        RolePermission(role_id=role.id, module="Opportunity", action="Create", data_scope="All"),
        RolePermission(role_id=role.id, module="Opportunity", action="Edit", data_scope="All"),
        RolePermission(role_id=role.id, module="Opportunity", action="View", data_scope="All"),
    ]
    for p in perms:
        if not db.query(RolePermission).filter(RolePermission.role_id == role.id, RolePermission.action == p.action).first():
            db.add(p)
    db.commit()
    db.close()

def create_base_opp(token):
    res = client.post(
        "/api/opportunities/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Deal with Wayne Enterprises", "expected_value": 100000}
    )
    return res.json()["id"]

def test_opportunity_creation_retrieval(admin_token, setup_opp_permissions):
    opp_id = create_base_opp(admin_token)
    assert opp_id > 0
    
    res = client.get("/api/opportunities/", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert len(res.json()) >= 1

def test_opportunity_won_workflow(admin_token):
    opp_id = create_base_opp(admin_token)
    
    # Opp -> Proposal
    res = client.post(f"/api/opportunities/{opp_id}/stage", headers={"Authorization": f"Bearer {admin_token}"}, json={"stage": "Proposal"})
    assert res.status_code == 200
    assert res.json()["stage"] == "Proposal"
    
    # Proposal -> Negotiation
    res = client.post(f"/api/opportunities/{opp_id}/stage", headers={"Authorization": f"Bearer {admin_token}"}, json={"stage": "Negotiation"})
    assert res.status_code == 200
    
    # Negotiation -> Won
    res = client.post(f"/api/opportunities/{opp_id}/stage", headers={"Authorization": f"Bearer {admin_token}"}, json={"stage": "Won"})
    assert res.status_code == 200
    assert res.json()["stage"] == "Won"
    
    # Verify Customer Creation
    db = SessionLocal()
    customer = db.query(Customer).filter(Customer.id == res.json()["customer_id"]).first()
    assert customer is not None
    assert customer.name == "Deal with Wayne Enterprises"
    db.close()

def test_opportunity_lost_workflow(admin_token):
    opp_id = create_base_opp(admin_token)
    
    # Missing Lost Reason
    res_fail = client.post(f"/api/opportunities/{opp_id}/stage", headers={"Authorization": f"Bearer {admin_token}"}, json={"stage": "Lost"})
    assert res_fail.status_code == 400
    assert "Lost Reason is required" in res_fail.json()["detail"]
    
    # With Lost Reason
    res = client.post(f"/api/opportunities/{opp_id}/stage", headers={"Authorization": f"Bearer {admin_token}"}, json={"stage": "Lost", "lost_reason": "Too expensive"})
    assert res.status_code == 200
    assert res.json()["stage"] == "Lost"
    assert res.json()["lost_reason"] == "Too expensive"

def test_invalid_stage_transitions(admin_token):
    opp_id = create_base_opp(admin_token)
    
    # Directly from Opportunity to Negotiation is not allowed in strict linear model unless configured.
    # Our dict says: "Opportunity": ["Proposal", "Lost", "Won"]. Negotiation is NOT allowed directly.
    res = client.post(f"/api/opportunities/{opp_id}/stage", headers={"Authorization": f"Bearer {admin_token}"}, json={"stage": "Negotiation"})
    assert res.status_code == 400
    assert "Invalid transition" in res.json()["detail"]

def test_locked_after_won_lost(admin_token):
    opp_id = create_base_opp(admin_token)
    client.post(f"/api/opportunities/{opp_id}/stage", headers={"Authorization": f"Bearer {admin_token}"}, json={"stage": "Lost", "lost_reason": "Test"})
    
    # Try editing
    res = client.put(f"/api/opportunities/{opp_id}", headers={"Authorization": f"Bearer {admin_token}"}, json={"expected_value": 5000})
    assert res.status_code == 400
    assert "Cannot edit" in res.json()["detail"]

def test_duplicate_customer_prevention(admin_token):
    opp_id1 = create_base_opp(admin_token)
    opp_id2 = client.post("/api/opportunities/", headers={"Authorization": f"Bearer {admin_token}"}, json={"name": "Deal with Wayne Enterprises", "expected_value": 50000}).json()["id"]
    
    # Win both
    res1 = client.post(f"/api/opportunities/{opp_id1}/stage", headers={"Authorization": f"Bearer {admin_token}"}, json={"stage": "Won"})
    res2 = client.post(f"/api/opportunities/{opp_id2}/stage", headers={"Authorization": f"Bearer {admin_token}"}, json={"stage": "Won"})
    
    assert res1.status_code == 200
    assert res2.status_code == 200
    
    # Should link to the same customer ID
    assert res1.json()["customer_id"] == res2.json()["customer_id"]

