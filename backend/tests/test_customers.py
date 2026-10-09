import pytest
from fastapi.testclient import TestClient
from main import app
from tests.conftest import TestingSessionLocal as SessionLocal
from app.models.domain import RolePermission, Role, Customer
import uuid

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_token():
    res = client.post("/api/auth/login", data={"username": "admin@crm360.com", "password": "Admin123!"})
    return res.json()["access_token"]

@pytest.fixture(scope="module")
def setup_customer_permissions():
    db = SessionLocal()
    role = db.query(Role).filter(Role.name == "System Administrator").first()
    perms = [
        RolePermission(role_id=role.id, module="Customer", action="Create", data_scope="All"),
        RolePermission(role_id=role.id, module="Customer", action="View", data_scope="All"),
        RolePermission(role_id=role.id, module="Customer", action="Edit", data_scope="All"),
        RolePermission(role_id=role.id, module="Contact", action="Create", data_scope="All"),
        RolePermission(role_id=role.id, module="Contact", action="View", data_scope="All"),
        RolePermission(role_id=role.id, module="Contact", action="Edit", data_scope="All"),
        RolePermission(role_id=role.id, module="Contact", action="Delete", data_scope="All"),
    ]
    for p in perms:
        if not db.query(RolePermission).filter(RolePermission.role_id == role.id, RolePermission.action == p.action, RolePermission.module == p.module).first():
            db.add(p)
    db.commit()
    db.close()

def create_base_customer(token):
    unique_name = f"Stark Industries {uuid.uuid4()}"
    payload = {"name": unique_name, "email": "contact@stark.com", "industry": "Defense"}
    res = client.post("/api/customers/", headers={"Authorization": f"Bearer {token}"}, json=payload)
    return res.json()

def test_customer_creation_duplicate_prevention(admin_token, setup_customer_permissions):
    customer = create_base_customer(admin_token)
    
    # Duplicate
    res2 = client.post("/api/customers/", headers={"Authorization": f"Bearer {admin_token}"}, json={"name": customer["name"]})
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]

def test_customer_update_retrieval(admin_token):
    customer = create_base_customer(admin_token)
    customer_id = customer["id"]
    
    # Update
    res = client.put(f"/api/customers/{customer_id}", headers={"Authorization": f"Bearer {admin_token}"}, json={"phone": "999888777"})
    assert res.status_code == 200
    assert res.json()["phone"] == "999888777"
    
    # Retrieve
    res_list = client.get("/api/customers/?search=Stark", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

def test_contact_crud(admin_token):
    customer = create_base_customer(admin_token)
    customer_id = customer["id"]
    
    # Create
    payload = {"name": "Tony Stark", "customer_id": customer_id, "email": "tony@stark.com"}
    res1 = client.post("/api/contacts/", headers={"Authorization": f"Bearer {admin_token}"}, json=payload)
    assert res1.status_code == 200
    contact_id = res1.json()["id"]
    
    # Read
    res2 = client.get(f"/api/contacts/?customer_id={customer_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert res2.status_code == 200
    assert any(c["name"] == "Tony Stark" for c in res2.json())
    
    # Update
    res3 = client.put(f"/api/contacts/{contact_id}", headers={"Authorization": f"Bearer {admin_token}"}, json={"designation": "CEO"})
    assert res3.status_code == 200
    assert res3.json()["designation"] == "CEO"
    
    # Delete
    res4 = client.delete(f"/api/contacts/{contact_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert res4.status_code == 200

