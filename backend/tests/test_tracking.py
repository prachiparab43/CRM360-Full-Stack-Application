import pytest
from fastapi.testclient import TestClient
from main import app
from app.db.session import SessionLocal
from app.models.domain import RolePermission, Role, Customer

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_token():
    res = client.post("/api/auth/login", data={"username": "admin@crm360.com", "password": "Admin123!"})
    return res.json()["access_token"]

@pytest.fixture(scope="module")
def setup_tracking_permissions():
    db = SessionLocal()
    role = db.query(Role).filter(Role.name == "System Administrator").first()
    perms = [
        ("GeoTracking", ["View"]),
        ("Visit", ["Create", "View", "Edit", "Delete"])
    ]
    for module, actions in perms:
        for action in actions:
            if not db.query(RolePermission).filter(RolePermission.role_id == role.id, RolePermission.action == action, RolePermission.module == module).first():
                db.add(RolePermission(role_id=role.id, module=module, action=action, data_scope="All"))
    db.commit()
    db.close()

def test_employee_checkin_checkout(admin_token):
    # Invalid coordinates check
    res_fail = client.post("/api/tracking/check-in", headers={"Authorization": f"Bearer {admin_token}"}, json={"latitude": 100, "longitude": 200})
    assert res_fail.status_code == 422 # Pydantic validation fails
    
    # Valid checkin
    res1 = client.post("/api/tracking/check-in", headers={"Authorization": f"Bearer {admin_token}"}, json={"latitude": 40.7128, "longitude": -74.0060, "location_info": "New York"})
    assert res1.status_code == 200
    assert res1.json()["type"] == "CheckIn"
    
    # Duplicate checkin prevention
    res2 = client.post("/api/tracking/check-in", headers={"Authorization": f"Bearer {admin_token}"}, json={"latitude": 40.7128, "longitude": -74.0060})
    assert res2.status_code == 400
    assert "Already checked in" in res2.json()["detail"]
    
    # Valid checkout
    res3 = client.post("/api/tracking/check-out", headers={"Authorization": f"Bearer {admin_token}"}, json={"latitude": 40.7128, "longitude": -74.0060})
    assert res3.status_code == 200
    assert res3.json()["type"] == "CheckOut"
    
    # Checkout without checkin prevention
    res4 = client.post("/api/tracking/check-out", headers={"Authorization": f"Bearer {admin_token}"}, json={"latitude": 40.7128, "longitude": -74.0060})
    assert res4.status_code == 400
    assert "Cannot check out" in res4.json()["detail"]

def test_visit_workflow(admin_token, setup_tracking_permissions):
    # Ensure there is a customer
    res = client.post("/api/customers/", headers={"Authorization": f"Bearer {admin_token}"}, json={"name": "Tracking Test Corp"})
    customer_id = res.json()["id"] if res.status_code == 200 else client.get("/api/customers/", headers={"Authorization": f"Bearer {admin_token}"}).json()[0]["id"]
    
    # Create Visit
    payload = {"customer_id": customer_id, "purpose": "Sales Pitch"}
    res1 = client.post("/api/visits/", headers={"Authorization": f"Bearer {admin_token}"}, json=payload)
    assert res1.status_code == 200
    visit_id = res1.json()["id"]
    
    # Check-in to visit
    loc = {"latitude": 34.0522, "longitude": -118.2437}
    res2 = client.post(f"/api/visits/{visit_id}/check-in", headers={"Authorization": f"Bearer {admin_token}"}, json=loc)
    assert res2.status_code == 200
    assert res2.json()["status"] == "InProgress"
    
    # Check-out of visit
    loc_out = {"latitude": 34.0522, "longitude": -118.2437, "remarks": "Went well"}
    res3 = client.post(f"/api/visits/{visit_id}/check-out", headers={"Authorization": f"Bearer {admin_token}"}, json=loc_out)
    assert res3.status_code == 200
    assert res3.json()["status"] == "Completed"
    assert res3.json()["remarks"] == "Went well"

def test_unauthorized_location_access():
    res = client.get("/api/tracking/latest")
    assert res.status_code == 401
