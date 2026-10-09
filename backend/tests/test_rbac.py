import pytest
from main import app
from tests.conftest import TestingSessionLocal as SessionLocal
from app.models.domain import Employee, Role, RolePermission, Lead
from app.core.security import get_password_hash

@pytest.fixture(scope="module")
def setup_limited_user():
    db = SessionLocal()
    # Create role with Own scope
    role = Role(name="Sales Rep", description="Limited Access")
    db.add(role)
    db.commit()
    db.refresh(role)
    
    # Give 'Own' scope for Leads
    perm_view = RolePermission(role_id=role.id, module="Lead", action="View", data_scope="Own")
    perm_edit = RolePermission(role_id=role.id, module="Lead", action="Edit", data_scope="Own")
    db.add(perm_view)
    db.add(perm_edit)
    db.commit()

    # Create limited user
    user1 = Employee(
        name="John Doe",
        email="john@crm360.com",
        password_hash=get_password_hash("Password123!"),
        role_id=role.id,
        status="Active"
    )
    # Create another user to own a different lead
    user2 = Employee(
        name="Jane Smith",
        email="jane@crm360.com",
        password_hash=get_password_hash("Password123!"),
        role_id=role.id,
        status="Active"
    )
    db.add(user1)
    db.add(user2)
    db.commit()
    db.refresh(user1)
    db.refresh(user2)
    
    # Create leads
    lead1 = Lead(name="Johns Lead", company="John Corp", assigned_employee_id=user1.id, status="New")
    lead2 = Lead(name="Janes Lead", company="Jane Corp", assigned_employee_id=user2.id, status="New")
    db.add(lead1)
    db.add(lead2)
    db.commit()
    db.refresh(lead1)
    db.refresh(lead2)
    
    yield {"user1": user1, "user2": user2, "lead1": lead1, "lead2": lead2}
    db.close()

def test_own_scope_cannot_edit_others_lead(client, setup_limited_user):
    # Login as John
    res = client.post("/api/auth/login", data={"username": "john@crm360.com", "password": "Password123!"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    
    data = setup_limited_user
    
    # John edits his own lead -> Should succeed
    res_own = client.put(f"/api/leads/{data['lead1'].id}", headers={"Authorization": f"Bearer {token}"}, json={"name": "Johns Lead Updated"})
    assert res_own.status_code == 200
    assert res_own.json()["name"] == "Johns Lead Updated"
    
    # John edits Jane's lead -> Should fail with 403 or 404 (due to scope filter)
    res_other = client.put(f"/api/leads/{data['lead2'].id}", headers={"Authorization": f"Bearer {token}"}, json={"name": "Hacked Lead"})
    assert res_other.status_code in [403, 404]
