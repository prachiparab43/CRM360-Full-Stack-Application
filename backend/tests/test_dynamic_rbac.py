import pytest
import json
from fastapi.testclient import TestClient
from main import app
from tests.conftest import TestingSessionLocal
from app.models.domain import Role, RolePermission, Employee, Company, Lead, Opportunity
from app.core.security import get_password_hash, create_access_token

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_token():
    res = client.post("/api/auth/login", data={"username": "admin@crm360.com", "password": "Admin123!"})
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["access_token"]

def test_roles_catalog_endpoint(admin_token):
    res = client.get("/api/roles/catalog", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "Company" in data["modules"]
    assert "Employee" in data["modules"]
    assert "Geo" in data["modules"]
    assert "Change Opportunity Stage" in data["actions"]["Opportunity"]
    assert "Geo.CheckIn" in data["actions"]["Geo"]
    assert data["restricted_scopes"]["Geo.CheckIn"] == ["Own"]

def test_invalid_action_rejected_on_role_create(admin_token):
    # Attempting to create role with nonexistent action
    payload = {
        "name": "Invalid Action Role",
        "permissions": [
            {"module": "Lead", "action": "NonExistentAction", "data_scope": "Own"}
        ]
    }
    res = client.post("/api/roles/", headers={"Authorization": f"Bearer {admin_token}"}, json=payload)
    assert res.status_code == 422
    assert "Invalid permission" in res.json()["detail"]

def test_invalid_scope_on_geo_checkin_rejected(admin_token):
    # Geo.CheckIn allows Own only
    payload = {
        "name": "Invalid Geo Scope Role",
        "permissions": [
            {"module": "Geo", "action": "Geo.CheckIn", "data_scope": "All"}
        ]
    }
    res = client.post("/api/roles/", headers={"Authorization": f"Bearer {admin_token}"}, json=payload)
    assert res.status_code == 422
    assert "Invalid permission" in res.json()["detail"]

def test_duplicate_role_name_rejected_409(admin_token):
    payload = {
        "name": "Duplicate Test Role",
        "permissions": [
            {"module": "Lead", "action": "View", "data_scope": "Own"}
        ]
    }
    res1 = client.post("/api/roles/", headers={"Authorization": f"Bearer {admin_token}"}, json=payload)
    assert res1.status_code == 200
    
    # Second create with duplicate name
    res2 = client.post("/api/roles/", headers={"Authorization": f"Bearer {admin_token}"}, json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]

def test_role_permission_history_audit(admin_token):
    payload = {
        "name": "Audited Role",
        "permissions": [
            {"module": "Lead", "action": "View", "data_scope": "Own"}
        ]
    }
    res = client.post("/api/roles/", headers={"Authorization": f"Bearer {admin_token}"}, json=payload)
    assert res.status_code == 200
    role_id = res.json()["id"]

    # Update permissions
    update_payload = {
        "permissions": [
            {"module": "Lead", "action": "View", "data_scope": "Team"},
            {"module": "Lead", "action": "Edit", "data_scope": "Own"}
        ]
    }
    res_update = client.put(f"/api/roles/{role_id}", headers={"Authorization": f"Bearer {admin_token}"}, json=update_payload)
    assert res_update.status_code == 200

    # Check permission history
    res_hist = client.get(f"/api/roles/{role_id}/permission-history", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_hist.status_code == 200
    history = res_hist.json()
    assert len(history) >= 2
    latest = history[0]
    assert latest["action"] == "Edit Permissions"
    assert any(p["action"] == "Edit" for p in latest["new_permissions"])

def test_inactive_role_blocks_access(admin_token):
    db = TestingSessionLocal()
    # Create an inactive role
    inactive_role = Role(name="Inactive User Role", description="Inactive", status="Inactive", is_system=False)
    db.add(inactive_role)
    db.commit()
    db.refresh(inactive_role)

    # Add View permission to this inactive role
    db.add(RolePermission(role_id=inactive_role.id, module="Lead", action="View", data_scope="All"))
    db.commit()

    # Create employee assigned to this inactive role
    emp = Employee(
        name="Inactive Role Employee",
        email="inactive_role_user@crm360.com",
        password_hash=get_password_hash("Password123!"),
        role_id=inactive_role.id,
        status="Active"
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    emp_id = emp.id
    db.close()

    token = create_access_token(emp_id)
    # Attempt to access /api/leads/
    res = client.get("/api/leads/", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
    assert "inactive" in res.json()["detail"].lower()

def test_scope_own_team_company_all():
    db = TestingSessionLocal()
    
    # 1. Setup Companies
    comp_a = Company(name="Test Scope Comp A")
    comp_b = Company(name="Test Scope Comp B")
    db.add_all([comp_a, comp_b])
    db.commit()
    db.refresh(comp_a)
    db.refresh(comp_b)

    # 2. Roles for each scope
    role_own = Role(name="Lead Scope Own", status="Active", is_system=False)
    role_team = Role(name="Lead Scope Team", status="Active", is_system=False)
    role_comp = Role(name="Lead Scope Comp", status="Active", is_system=False)
    role_all = Role(name="Lead Scope All", status="Active", is_system=False)
    db.add_all([role_own, role_team, role_comp, role_all])
    db.commit()

    db.add(RolePermission(role_id=role_own.id, module="Lead", action="View", data_scope="Own"))
    db.add(RolePermission(role_id=role_team.id, module="Lead", action="View", data_scope="Team"))
    db.add(RolePermission(role_id=role_comp.id, module="Lead", action="View", data_scope="Company"))
    db.add(RolePermission(role_id=role_all.id, module="Lead", action="View", data_scope="All"))
    db.commit()

    role_own_id = role_own.id
    role_team_id = role_team.id
    role_comp_id = role_comp.id
    role_all_id = role_all.id

    # 3. Hierarchy: Manager M -> Direct report S1 -> Indirect report S2
    # Peer P in comp A (not in M's team)
    # Outsider O in comp B
    mgr = Employee(name="Manager M", email="mgr_m@scope.com", company_id=comp_a.id, status="Active", role_id=role_team_id)
    db.add(mgr)
    db.commit()
    db.refresh(mgr)
    mgr_id = mgr.id

    sub1 = Employee(name="Subordinate S1", email="sub1@scope.com", company_id=comp_a.id, manager_id=mgr_id, status="Active", role_id=role_own_id)
    db.add(sub1)
    db.commit()
    db.refresh(sub1)
    sub1_id = sub1.id

    sub2 = Employee(name="Subordinate S2", email="sub2@scope.com", company_id=comp_a.id, manager_id=sub1_id, status="Active", role_id=role_own_id)
    peer = Employee(name="Peer P", email="peer_p@scope.com", company_id=comp_a.id, manager_id=None, status="Active", role_id=role_own_id)
    outsider = Employee(name="Outsider O", email="outsider_o@scope.com", company_id=comp_b.id, manager_id=None, status="Active", role_id=role_own_id)
    db.add_all([sub2, peer, outsider])
    db.commit()
    db.refresh(sub2)
    db.refresh(peer)
    db.refresh(outsider)

    # 4. Leads created for each
    lead_m = Lead(name="Lead M", assigned_employee_id=mgr_id, status="New")
    lead_s1 = Lead(name="Lead S1", assigned_employee_id=sub1_id, status="New")
    lead_s2 = Lead(name="Lead S2", assigned_employee_id=sub2.id, status="New")
    lead_p = Lead(name="Lead P", assigned_employee_id=peer.id, status="New")
    lead_o = Lead(name="Lead O", assigned_employee_id=outsider.id, status="New")
    db.add_all([lead_m, lead_s1, lead_s2, lead_p, lead_o])
    db.commit()
    db.close()

    token_mgr = create_access_token(mgr_id)

    # Test Team scope: Manager M should see lead_m, lead_s1, lead_s2 (recursive CTE!), but NOT lead_p or lead_o
    res_team = client.get("/api/leads/", headers={"Authorization": f"Bearer {token_mgr}"})
    assert res_team.status_code == 200
    lead_names = [l["name"] for l in res_team.json().get("items", res_team.json())]
    assert "Lead M" in lead_names
    assert "Lead S1" in lead_names
    assert "Lead S2" in lead_names
    assert "Lead P" not in lead_names
    assert "Lead O" not in lead_names

    # Test Own scope: Switch M's role to role_own
    db = TestingSessionLocal()
    mgr_rec = db.query(Employee).filter(Employee.id == mgr_id).first()
    mgr_rec.role_id = role_own_id
    db.commit()
    db.close()

    res_own = client.get("/api/leads/", headers={"Authorization": f"Bearer {token_mgr}"})
    assert res_own.status_code == 200
    own_lead_names = [l["name"] for l in res_own.json().get("items", res_own.json())]
    assert "Lead M" in own_lead_names
    assert "Lead S1" not in own_lead_names
    assert "Lead S2" not in own_lead_names
    assert "Lead P" not in own_lead_names
    assert "Lead O" not in own_lead_names

    # Test Company scope: Switch M's role to role_comp
    db = TestingSessionLocal()
    mgr_rec = db.query(Employee).filter(Employee.id == mgr_id).first()
    mgr_rec.role_id = role_comp_id
    db.commit()
    db.close()

    res_comp = client.get("/api/leads/", headers={"Authorization": f"Bearer {token_mgr}"})
    assert res_comp.status_code == 200
    comp_lead_names = [l["name"] for l in res_comp.json().get("items", res_comp.json())]
    assert "Lead M" in comp_lead_names
    assert "Lead S1" in comp_lead_names
    assert "Lead S2" in comp_lead_names
    assert "Lead P" in comp_lead_names
    assert "Lead O" not in comp_lead_names

    # Test All scope: Switch M's role to role_all
    db = TestingSessionLocal()
    mgr_rec = db.query(Employee).filter(Employee.id == mgr_id).first()
    mgr_rec.role_id = role_all_id
    db.commit()
    db.close()

    res_all = client.get("/api/leads/", headers={"Authorization": f"Bearer {token_mgr}"})
    assert res_all.status_code == 200
    all_lead_names = [l["name"] for l in res_all.json().get("items", res_all.json())]
    assert "Lead M" in all_lead_names
    assert "Lead S1" in all_lead_names
    assert "Lead S2" in all_lead_names
    assert "Lead P" in all_lead_names
    assert "Lead O" in all_lead_names

def test_privilege_escalation_prevented(admin_token):
    db = TestingSessionLocal()
    # Limited role with only Employee:Create and Role:Assign (Own)
    limited_role = Role(name="Limited HR Role", status="Active", is_system=False)
    db.add(limited_role)
    db.commit()
    db.refresh(limited_role)

    db.add(RolePermission(role_id=limited_role.id, module="Employee", action="Create", data_scope="All"))
    db.add(RolePermission(role_id=limited_role.id, module="Role", action="Assign", data_scope="All"))
    db.add(RolePermission(role_id=limited_role.id, module="Lead", action="View", data_scope="Own"))
    db.commit()

    # Elevated role having Lead:View All and Company:Delete All
    elevated_role = Role(name="Elevated Power Role", status="Active", is_system=False)
    db.add(elevated_role)
    db.commit()
    db.refresh(elevated_role)
    elevated_role_id = elevated_role.id

    db.add(RolePermission(role_id=elevated_role.id, module="Lead", action="View", data_scope="All"))
    db.add(RolePermission(role_id=elevated_role.id, module="Company", action="Delete", data_scope="All"))
    db.commit()

    hr_user = Employee(
        name="HR Specialist",
        email="hr_user@crm360.com",
        password_hash=get_password_hash("Password123!"),
        role_id=limited_role.id,
        status="Active"
    )
    db.add(hr_user)
    db.commit()
    db.refresh(hr_user)
    hr_user_id = hr_user.id
    db.close()

    hr_token = create_access_token(hr_user_id)

    # Attempt 1: HR Specialist attempts to create an employee with the elevated role (possessing Company:Delete)
    create_payload = {
        "name": "Attacker Puppet",
        "email": "puppet@crm360.com",
        "password": "Password123!",
        "role_id": elevated_role_id
    }
    res_esc = client.post("/api/employees/", headers={"Authorization": f"Bearer {hr_token}"}, json=create_payload)
    assert res_esc.status_code == 403
    assert "Cannot assign a role that possesses permissions" in res_esc.json()["detail"]

    # Attempt 2: User without Role:Assign tries to assign a role
    db = TestingSessionLocal()
    no_assign_role = Role(name="No Assign Role", status="Active", is_system=False)
    db.add(no_assign_role)
    db.commit()
    db.refresh(no_assign_role)
    db.add(RolePermission(role_id=no_assign_role.id, module="Employee", action="Create", data_scope="All"))
    db.commit()

    no_assign_user = Employee(
        name="No Assign User",
        email="no_assign@crm360.com",
        password_hash=get_password_hash("Password123!"),
        role_id=no_assign_role.id,
        status="Active"
    )
    db.add(no_assign_user)
    db.commit()
    db.refresh(no_assign_user)
    no_assign_id = no_assign_user.id
    db.close()

    no_assign_token = create_access_token(no_assign_id)
    res_no_assign = client.post("/api/employees/", headers={"Authorization": f"Bearer {no_assign_token}"}, json=create_payload)
    assert res_no_assign.status_code == 403
    assert "Role Assign permission required" in res_no_assign.json()["detail"]

def test_last_admin_protection(admin_token):
    db = TestingSessionLocal()
    # Find the seeded system admin employee
    admin_emp = db.query(Employee).filter(Employee.email == "admin@crm360.com").first()
    assert admin_emp is not None
    admin_emp_id = admin_emp.id
    system_role = db.query(Role).filter(Role.id == admin_emp.role_id).first()
    assert system_role.is_system is True
    system_role_id = system_role.id

    # Deactivate any other test employees holding Role Edit/Assign
    admin_perms = db.query(RolePermission.role_id).filter(
        RolePermission.module == "Role",
        RolePermission.action.in_(["Edit", "Assign"])
    ).distinct().all()
    admin_role_ids = [r[0] for r in admin_perms]
    other_admins = db.query(Employee).filter(
        Employee.status == "Active",
        Employee.role_id.in_(admin_role_ids),
        Employee.id != admin_emp_id
    ).all()
    for o in other_admins:
        o.status = "Inactive"
    db.commit()
    db.close()

    # 1. Attempt to deactivate the system role
    res_deact = client.post(f"/api/roles/{system_role_id}/deactivate", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_deact.status_code == 400
    assert "System role cannot be deactivated" in res_deact.json()["detail"]

    # 2. Attempt to edit the system role
    res_edit = client.put(f"/api/roles/{system_role_id}", headers={"Authorization": f"Bearer {admin_token}"}, json={"name": "Renamed System Admin"})
    assert res_edit.status_code == 400
    assert "System role cannot be modified" in res_edit.json()["detail"]

    # 3. Attempt to delete the system role
    res_del = client.delete(f"/api/roles/{system_role_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_del.status_code == 400
    assert "System role cannot be deleted" in res_del.json()["detail"]

    # 4. Attempt to deactivate the last admin employee
    res_deact_emp = client.put(f"/api/employees/{admin_emp_id}", headers={"Authorization": f"Bearer {admin_token}"}, json={"status": "Inactive"})
    assert res_deact_emp.status_code == 400
    assert "Cannot deactivate the last active employee" in res_deact_emp.json()["detail"]

    # 5. Attempt to delete the last admin employee
    res_del_emp = client.delete(f"/api/employees/{admin_emp_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_del_emp.status_code == 400
    assert "Cannot delete the last active employee" in res_del_emp.json()["detail"]

def test_geo_tracking_permissions(admin_token):
    db = TestingSessionLocal()
    # Create role without Geo.CheckIn permission
    no_geo_role = Role(name="No Geo Role", status="Active", is_system=False)
    db.add(no_geo_role)
    db.commit()
    db.refresh(no_geo_role)

    no_geo_emp = Employee(
        name="No Geo User",
        email="no_geo_user@crm360.com",
        password_hash=get_password_hash("Password123!"),
        role_id=no_geo_role.id,
        status="Active"
    )
    db.add(no_geo_emp)
    db.commit()
    db.refresh(no_geo_emp)
    no_geo_id = no_geo_emp.id
    db.close()

    no_geo_token = create_access_token(no_geo_id)

    # Check-in without Geo.CheckIn permission -> 403
    loc = {"latitude": 37.7749, "longitude": -122.4194}
    res_fail = client.post("/api/tracking/check-in", headers={"Authorization": f"Bearer {no_geo_token}"}, json=loc)
    assert res_fail.status_code == 403
    assert "Not authorized to Geo.CheckIn in Geo" in res_fail.json()["detail"]

    # Ensure admin is checked out before checkin
    client.post("/api/tracking/check-out", headers={"Authorization": f"Bearer {admin_token}"}, json=loc)

    # Admin with Geo.CheckIn permission -> 200
    res_ok = client.post("/api/tracking/check-in", headers={"Authorization": f"Bearer {admin_token}"}, json=loc)
    assert res_ok.status_code == 200
    assert res_ok.json()["type"] == "CheckIn"

    # Checkout with Geo.CheckOut
    res_out = client.post("/api/tracking/check-out", headers={"Authorization": f"Bearer {admin_token}"}, json=loc)
    assert res_out.status_code == 200
    assert res_out.json()["type"] == "CheckOut"
