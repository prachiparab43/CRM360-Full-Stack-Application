import pytest
from fastapi.testclient import TestClient
from main import app
from tests.conftest import TestingSessionLocal as SessionLocal
from app.models.domain import Role, RolePermission, Employee, Company, Lead, Opportunity, Customer, Contact, Task, Meeting
from app.core.security import get_password_hash
from datetime import date, timedelta
import uuid

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_token():
    res = client.post("/api/auth/login", data={"username": "admin@crm360.com", "password": "Admin123!"})
    assert res.status_code == 200
    return res.json()["access_token"]

@pytest.fixture(scope="module")
def normal_user_token():
    db = SessionLocal()
    # Create a limited sales rep role
    rep_role = db.query(Role).filter(Role.name == "Limited Sales Rep").first()
    if not rep_role:
        rep_role = Role(name="Limited Sales Rep", description="Basic access", status="Active")
        db.add(rep_role)
        db.commit()
        db.refresh(rep_role)
        
        # Grant only Own scope on Lead View/Create
        perms = [
            RolePermission(role_id=rep_role.id, module="Lead", action="Create", data_scope="Own"),
            RolePermission(role_id=rep_role.id, module="Lead", action="View", data_scope="Own"),
            RolePermission(role_id=rep_role.id, module="Lead", action="Edit", data_scope="Own"),
        ]
        db.add_all(perms)
        db.commit()
        
    rep_user = db.query(Employee).filter(Employee.email == "rep@crm360.com").first()
    if not rep_user:
        rep_user = Employee(
            name="Sales Rep One",
            email="rep@crm360.com",
            password_hash=get_password_hash("RepPass123!"),
            role_id=rep_role.id,
            status="Active"
        )
        db.add(rep_user)
        db.commit()
    db.close()
    
    res = client.post("/api/auth/login", data={"username": "rep@crm360.com", "password": "RepPass123!"})
    assert res.status_code == 200
    return res.json()["access_token"]

# --- 1. AUTH & SECURITY TESTS ---

def test_login_invalid_password():
    res = client.post("/api/auth/login", data={"username": "admin@crm360.com", "password": "WrongPassword"})
    assert res.status_code == 400
    assert "Incorrect email or password" in res.json()["detail"]

def test_login_nonexistent_user():
    res = client.post("/api/auth/login", data={"username": "ghost@crm360.com", "password": "Password123!"})
    assert res.status_code == 400
    assert "Incorrect email or password" in res.json()["detail"]

def test_unauthenticated_request_fails():
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 401

def test_invalid_bearer_token_fails():
    res = client.get("/api/dashboard/summary", headers={"Authorization": "Bearer invalid_garbage_token"})
    assert res.status_code == 403

def test_normal_user_forbidden_from_admin_roles(normal_user_token):
    res = client.get("/api/roles/", headers={"Authorization": f"Bearer {normal_user_token}"})
    assert res.status_code == 403

def test_normal_user_forbidden_from_admin_companies(normal_user_token):
    res = client.get("/api/companies/", headers={"Authorization": f"Bearer {normal_user_token}"})
    assert res.status_code == 403

def test_normal_user_forbidden_from_admin_employees(normal_user_token):
    res = client.get("/api/employees/", headers={"Authorization": f"Bearer {normal_user_token}"})
    assert res.status_code == 403

# --- 2. ROLES & PERMISSIONS MODULE CRUD ---

def test_role_crud_and_validation(admin_token):
    # Validation: missing name
    bad_res = client.post("/api/roles/", headers={"Authorization": f"Bearer {admin_token}"}, json={})
    assert bad_res.status_code == 422
    
    # Create valid role
    role_name = f"Custom Role {uuid.uuid4().hex[:6]}"
    create_res = client.post(
        "/api/roles/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": role_name,
            "description": "Custom role for testing",
            "status": "Active",
            "permissions": [
                {"module": "Lead", "action": "View", "data_scope": "Team"},
                {"module": "Lead", "action": "Edit", "data_scope": "Team"}
            ]
        }
    )
    assert create_res.status_code == 200
    role_data = create_res.json()
    role_id = role_data["id"]
    assert role_data["name"] == role_name
    assert len(role_data["permissions"]) == 2
    
    # Retrieve role by ID
    get_res = client.get(f"/api/roles/{role_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert get_res.status_code == 200
    assert get_res.json()["name"] == role_name
    
    # Update role
    update_res = client.put(
        f"/api/roles/{role_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "description": "Updated description",
            "permissions": [
                {"module": "Lead", "action": "View", "data_scope": "All"}
            ]
        }
    )
    assert update_res.status_code == 200
    assert update_res.json()["description"] == "Updated description"
    assert len(update_res.json()["permissions"]) == 1
    
    # 404 on nonexistent role ID
    not_found_res = client.get("/api/roles/999999", headers={"Authorization": f"Bearer {admin_token}"})
    assert not_found_res.status_code == 404

# --- 3. COMPANIES & EMPLOYEES VALIDATION & RELATIONS ---

def test_employee_validation_invalid_email(admin_token):
    res = client.post(
        "/api/employees/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Bad Email User", "email": "not-an-email", "password": "Password123!"}
    )
    assert res.status_code == 422

def test_employee_duplicate_email(admin_token):
    email = f"duplicate_{uuid.uuid4().hex[:6]}@crm360.com"
    res1 = client.post(
        "/api/employees/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "User One", "email": email, "password": "Password123!"}
    )
    assert res1.status_code == 200
    
    res2 = client.post(
        "/api/employees/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "User Two", "email": email, "password": "Password123!"}
    )
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]

# --- 4. LEADS, OPPORTUNITIES, CUSTOMERS, CONTACTS WORKFLOW ---

def test_full_lead_to_customer_contact_workflow(admin_token):
    # 1. Create Lead
    unique_company = f"Global Tech {uuid.uuid4().hex[:6]}"
    lead_res = client.post(
        "/api/leads/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Alice Wonder", "company": unique_company, "email": "alice@wonder.com", "phone": "555-1234"}
    )
    assert lead_res.status_code == 200
    lead = lead_res.json()
    lead_id = lead["id"]
    
    # 2. Search Lead
    search_res = client.get(f"/api/leads/?search={unique_company}", headers={"Authorization": f"Bearer {admin_token}"})
    assert search_res.status_code == 200
    assert any(l["id"] == lead_id for l in search_res.json())
    
    # 3. Qualify Lead -> Creates Opportunity
    qual_res = client.post(
        f"/api/leads/{lead_id}/qualify",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"expected_value": 75000, "name": f"Deal with {unique_company}"}
    )
    assert qual_res.status_code == 200
    assert qual_res.json()["status"] == "Qualified"
    
    # 4. Find Opportunity linked to Lead
    db = SessionLocal()
    opp = db.query(Opportunity).filter(Opportunity.lead_id == lead_id).first()
    assert opp is not None
    opp_id = opp.id
    db.close()
    
    # 5. Opportunity Stage Transitions -> Won -> Automatically Creates Customer
    # Valid transition to Proposal
    stage_res1 = client.post(
        f"/api/opportunities/{opp_id}/stage",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"stage": "Proposal"}
    )
    assert stage_res1.status_code == 200
    assert stage_res1.json()["stage"] == "Proposal"
    
    # Valid transition to Won
    stage_res2 = client.post(
        f"/api/opportunities/{opp_id}/stage",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"stage": "Won"}
    )
    assert stage_res2.status_code == 200
    assert stage_res2.json()["stage"] == "Won"
    
    # Verify Customer was created with unique company name
    cust_res = client.get(f"/api/customers/?search={unique_company}", headers={"Authorization": f"Bearer {admin_token}"})
    assert cust_res.status_code == 200
    assert len(cust_res.json()) >= 1
    customer_id = cust_res.json()[0]["id"]
    
    # 6. Create Contact under this new Customer
    contact_res = client.post(
        "/api/contacts/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Alice Wonder", "email": "alice@wonder.com", "customer_id": customer_id, "designation": "CTO"}
    )
    assert contact_res.status_code == 200
    contact_id = contact_res.json()["id"]
    
    # 7. Update Contact
    contact_update = client.put(
        f"/api/contacts/{contact_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"phone": "987-654-3210"}
    )
    assert contact_update.status_code == 200
    assert contact_update.json()["phone"] == "987-654-3210"
    
    # 8. Delete Contact
    contact_del = client.delete(f"/api/contacts/{contact_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert contact_del.status_code == 200
    
    # Verify Contact is gone
    contact_verify = client.get(f"/api/contacts/?customer_id={customer_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert not any(c["id"] == contact_id for c in contact_verify.json())

# --- 5. TASKS, MEETINGS & OVERDUE FILTERING ---

def test_tasks_crud_and_overdue_filter(admin_token):
    # Missing title validation
    bad_res = client.post("/api/tasks/", headers={"Authorization": f"Bearer {admin_token}"}, json={})
    assert bad_res.status_code == 422
    
    # Create past task (overdue)
    yesterday = (date.today() - timedelta(days=2)).isoformat()
    t_res = client.post(
        "/api/tasks/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"title": "Follow up urgently", "due_date": yesterday, "priority": "High", "assigned_employee_id": 1}
    )
    assert t_res.status_code == 200
    task_id = t_res.json()["id"]
    
    # Filter overdue tasks
    overdue_res = client.get("/api/tasks/?overdue=true", headers={"Authorization": f"Bearer {admin_token}"})
    assert overdue_res.status_code == 200
    assert any(t["id"] == task_id for t in overdue_res.json())
    
    # Update task to Completed
    complete_res = client.put(
        f"/api/tasks/{task_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "Completed"}
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "Completed"
    assert complete_res.json()["completion_date"] is not None

def test_meetings_validation_invalid_times(admin_token):
    # End time before start time
    today = date.today().isoformat()
    bad_res = client.post(
        "/api/meetings/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "subject": "Invalid Meeting",
            "date": today,
            "start_time": "14:00:00",
            "end_time": "13:00:00",
            "employee_id": 1
        }
    )
    assert bad_res.status_code == 400
    assert "Start time must be before end time" in bad_res.json()["detail"]

# --- 6. REPORTS EXPORT ---

def test_reports_export_opportunities(admin_token):
    res = client.get("/api/reports/opportunities/export", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "attachment; filename=opportunities_export.csv" in res.headers["content-disposition"]
    content = res.text
    assert "ID,Name,Expected Value,Stage,Assigned Employee ID" in content
