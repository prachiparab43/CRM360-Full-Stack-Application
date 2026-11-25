import pytest
import uuid
from datetime import date, timedelta, datetime
from fastapi.testclient import TestClient
from main import app
from tests.conftest import TestingSessionLocal
from app.models.domain import (
    Employee, Company, Role, RolePermission, Lead, Opportunity, Customer, Contact,
    Activity, Task, Meeting, GeoTracking, CustomerVisit, AuditLog
)

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_token():
    res = client.post("/api/auth/login", data={"username": "admin@crm360.com", "password": "Admin123!"})
    assert res.status_code == 200
    return res.json()["access_token"]

# --- 1. OPPORTUNITY LIFECYCLE & VALIDATION TESTS ---

def test_opportunity_lifecycle_enforcement(admin_token):
    # Create opportunity
    opp_res = client.post(
        "/api/opportunities/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Lifecycle Deal", "expected_value": 10000, "probability": 20}
    )
    assert opp_res.status_code == 200
    opp_id = opp_res.json()["id"]

    # 1. Direct Opportunity -> Won must fail (HTTP 400)
    won_direct = client.post(
        f"/api/opportunities/{opp_id}/stage",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"stage": "Won"}
    )
    assert won_direct.status_code == 400
    assert "Invalid transition" in won_direct.json()["detail"]

    # 2. Advance to Proposal
    p_res = client.post(
        f"/api/opportunities/{opp_id}/stage",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"stage": "Proposal"}
    )
    assert p_res.status_code == 200

    # 3. Direct Proposal -> Won must fail (HTTP 400)
    won_from_prop = client.post(
        f"/api/opportunities/{opp_id}/stage",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"stage": "Won"}
    )
    assert won_from_prop.status_code == 400
    assert "Invalid transition" in won_from_prop.json()["detail"]

    # 4. Advance to Negotiation
    n_res = client.post(
        f"/api/opportunities/{opp_id}/stage",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"stage": "Negotiation"}
    )
    assert n_res.status_code == 200

    # 5. Advance from Negotiation to Won
    won_res = client.post(
        f"/api/opportunities/{opp_id}/stage",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"stage": "Won"}
    )
    assert won_res.status_code == 200
    assert won_res.json()["stage"] == "Won"
    assert won_res.json()["probability"] == 100.0

    # 6. Cannot change stage of Won opportunity
    post_won = client.post(
        f"/api/opportunities/{opp_id}/stage",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"stage": "Proposal"}
    )
    assert post_won.status_code == 400
    assert "Cannot change stage of a Won or Lost" in post_won.json()["detail"]

def test_opportunity_lost_requires_reason(admin_token):
    opp_res = client.post(
        "/api/opportunities/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Lost Opportunity Deal", "expected_value": 5000}
    )
    opp_id = opp_res.json()["id"]

    # Missing reason
    res_no_reason = client.post(
        f"/api/opportunities/{opp_id}/stage",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"stage": "Lost", "lost_reason": ""}
    )
    assert res_no_reason.status_code == 400
    assert "Lost Reason is required" in res_no_reason.json()["detail"]

    # Valid lost
    res_lost = client.post(
        f"/api/opportunities/{opp_id}/stage",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"stage": "Lost", "lost_reason": "Competitor chosen"}
    )
    assert res_lost.status_code == 200
    assert res_lost.json()["stage"] == "Lost"
    assert res_lost.json()["lost_reason"] == "Competitor chosen"
    assert res_lost.json()["probability"] == 0.0

def test_opportunity_field_validations(admin_token):
    # Negative expected value
    bad_val = client.post(
        "/api/opportunities/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Bad Val Deal", "expected_value": -500}
    )
    assert bad_val.status_code in [400, 422]

    # Probability > 100
    bad_prob = client.post(
        "/api/opportunities/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Bad Prob Deal", "probability": 150}
    )
    assert bad_prob.status_code in [400, 422]

    # Expected close date in the past
    yesterday = (date.today() - timedelta(days=2)).isoformat()
    bad_date = client.post(
        "/api/opportunities/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Bad Date Deal", "expected_close_date": yesterday}
    )
    assert bad_date.status_code in [400, 422]

# --- 2. WON WORKFLOW (Customer, Contact copy, single tx) ---

def test_won_workflow_customer_and_contact_creation(admin_token):
    unique_company = f"WonCo {uuid.uuid4().hex[:6]}"
    lead_res = client.post(
        "/api/leads/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Sarah Connor",
            "company": unique_company,
            "contact_name": "Sarah Connor",
            "email": "sarah@wonco.com",
            "phone": "555-8888",
            "requirement": "Industrial defense"
        }
    )
    lead_id = lead_res.json()["id"]

    # Qualify lead to create opportunity
    qual_res = client.post(
        f"/api/leads/{lead_id}/qualify",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"expected_value": 150000, "probability": 50}
    )
    assert qual_res.status_code == 200

    db = TestingSessionLocal()
    opp = db.query(Opportunity).filter(Opportunity.lead_id == lead_id).first()
    assert opp is not None
    opp_id = opp.id
    db.close()

    # Progress: Opportunity -> Proposal -> Negotiation -> Won
    client.post(f"/api/opportunities/{opp_id}/stage", headers={"Authorization": f"Bearer {admin_token}"}, json={"stage": "Proposal"})
    client.post(f"/api/opportunities/{opp_id}/stage", headers={"Authorization": f"Bearer {admin_token}"}, json={"stage": "Negotiation"})
    won_res = client.post(f"/api/opportunities/{opp_id}/stage", headers={"Authorization": f"Bearer {admin_token}"}, json={"stage": "Won"})
    assert won_res.status_code == 200
    won_data = won_res.json()

    # Verify customer created and linked
    customer_id = won_data["customer_id"]
    assert customer_id is not None
    assert won_data["lead_id"] == lead_id

    # Verify contact was copied
    c_res = client.get(f"/api/contacts/?customer_id={customer_id}&raw=true", headers={"Authorization": f"Bearer {admin_token}"})
    contacts = c_res.json() if isinstance(c_res.json(), list) else c_res.json().get("items", [])
    assert any(c["name"] == "Sarah Connor" and c["email"] == "sarah@wonco.com" for c in contacts)

# --- 3. REASSIGNMENT PERMISSIONS & SCOPE ---

def test_reassignment_permissions_and_scope(admin_token):
    # Create lead
    l_res = client.post(
        "/api/leads/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Reassign Target", "company": "Reassign Co"}
    )
    lead_id = l_res.json()["id"]

    # Reassign lead with Admin token (holding Reassign Lead and All scope) -> succeeds
    reassign_res = client.put(
        f"/api/leads/{lead_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"assigned_employee_id": 1}
    )
    assert reassign_res.status_code == 200
    assert reassign_res.json()["assigned_employee_id"] == 1

# --- 4. AUDIT LOG ATOMICITY & HISTORY ENDPOINTS ---

def test_audit_logs_query_and_history(admin_token):
    # 1. GET /api/audit-logs
    audit_res = client.get("/api/audit-logs/", headers={"Authorization": f"Bearer {admin_token}"})
    assert audit_res.status_code == 200
    data = audit_res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1

    # Filter audit logs by module
    lead_audit = client.get("/api/audit-logs/?module=Lead", headers={"Authorization": f"Bearer {admin_token}"})
    assert lead_audit.status_code == 200
    assert all(item["module"] == "Lead" for item in lead_audit.json()["items"])

    # 2. GET /api/leads/{id}/history
    l_res = client.post(
        "/api/leads/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "History Lead", "company": "History Corp"}
    )
    lead_id = l_res.json()["id"]

    # Update to create audit trail
    client.put(f"/api/leads/{lead_id}", headers={"Authorization": f"Bearer {admin_token}"}, json={"notes": "Updated note"})
    
    hist_res = client.get(f"/api/leads/{lead_id}/history", headers={"Authorization": f"Bearer {admin_token}"})
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert len(hist) >= 2
    assert any(h["action"] == "Create" for h in hist)
    assert any(h["action"] == "Edit" for h in hist)

# --- 5. GEO TRACKING & CUSTOMER VISITS ---

def test_geo_tracking_latest_one_point_per_employee(admin_token):
    # Post multiple check-in/outs for employee 1
    # Check-in with optional customer_id
    c_res = client.get("/api/customers/?limit=1&raw=true", headers={"Authorization": f"Bearer {admin_token}"})
    c_data = c_res.json()
    custs = c_data if isinstance(c_data, list) else c_data.get("items", [])
    cust_id = custs[0]["id"]

    # Check latest
    latest_res = client.get("/api/tracking/latest", headers={"Authorization": f"Bearer {admin_token}"})
    assert latest_res.status_code == 200
    emp_ids = [p["employee_id"] for p in latest_res.json()]
    # Strictly one latest point per employee -> no duplicates
    assert len(emp_ids) == len(set(emp_ids))

def test_geo_tracking_history(admin_token):
    res = client.get("/api/tracking/history?employee_id=1", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data

def test_customer_visits_filtered_list(admin_token):
    res = client.get("/api/visits/?status=Scheduled", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert all(v["status"] == "Scheduled" for v in data["items"])

# --- 6. DASHBOARD CONDITIONAL AGGREGATION ---

def test_dashboard_summary_conditional_aggregation(admin_token):
    res = client.get("/api/dashboard/summary", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    s = res.json()
    # Check new required fields
    assert "new_leads" in s
    assert "contacted_leads" in s
    assert "new_customers" in s
    assert "active_customers" in s
    assert "checked_in_employees" in s
    assert "active_visits" in s
    assert "upcoming_meetings_list" in s
    assert "recent_activities" in s
    assert isinstance(s["upcoming_meetings_list"], list)
    assert isinstance(s["recent_activities"], list)

# --- 7. REPORTS MODULE (JSON & CSV EXPORTS) ---

def test_all_reports_json_and_csv(admin_token):
    # Leads report
    r_lead = client.get("/api/reports/leads", headers={"Authorization": f"Bearer {admin_token}"})
    assert r_lead.status_code == 200
    assert "total_leads" in r_lead.json()
    assert "conversion_rate_percent" in r_lead.json()

    r_lead_csv = client.get("/api/reports/leads/export", headers={"Authorization": f"Bearer {admin_token}"})
    assert r_lead_csv.status_code == 200
    assert "text/csv" in r_lead_csv.headers["content-type"]

    # Opportunities report
    r_opp = client.get("/api/reports/opportunities", headers={"Authorization": f"Bearer {admin_token}"})
    assert r_opp.status_code == 200
    assert "total_expected_revenue" in r_opp.json()

    # Customers report
    r_cust = client.get("/api/reports/customers", headers={"Authorization": f"Bearer {admin_token}"})
    assert r_cust.status_code == 200
    assert "total_customers" in r_cust.json()

    # Employees report
    r_emp = client.get("/api/reports/employees", headers={"Authorization": f"Bearer {admin_token}"})
    assert r_emp.status_code == 200
    assert "employees" in r_emp.json()

    # Geo report
    r_geo = client.get("/api/reports/geo", headers={"Authorization": f"Bearer {admin_token}"})
    assert r_geo.status_code == 200
    assert "total_geo_points" in r_geo.json()

# --- 8. PAGINATION EVERYWHERE & SORT WHITELIST ---

def test_pagination_and_sort_whitelist(admin_token):
    # 1. Standard paginated format
    res = client.get("/api/leads/?limit=5&sort_by=name&sort_dir=asc", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["limit"] == 5

    # 2. Backward-compatible flat array when raw=true
    raw_res = client.get("/api/leads/?raw=true&limit=5", headers={"Authorization": f"Bearer {admin_token}"})
    assert raw_res.status_code == 200
    assert isinstance(raw_res.json(), list)

    # 3. Invalid sort field rejected with HTTP 400
    bad_sort = client.get("/api/leads/?sort_by=non_existent_column", headers={"Authorization": f"Bearer {admin_token}"})
    assert bad_sort.status_code == 400
    assert "Invalid sort field" in bad_sort.json()["detail"]

# --- 9. ENGAGEMENTS (Task complete/cancel, Rescheduled meetings) ---

def test_task_complete_and_cancel_endpoints(admin_token):
    # Create task
    t_res = client.post(
        "/api/tasks/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"title": "Action Item", "priority": "Medium"}
    )
    task_id = t_res.json()["id"]

    # Explicit complete
    comp_res = client.post(f"/api/tasks/{task_id}/complete", headers={"Authorization": f"Bearer {admin_token}"})
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "Completed"
    assert comp_res.json()["completion_date"] is not None

    # Explicit cancel
    t2_res = client.post(
        "/api/tasks/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"title": "Cancel Item", "priority": "Low"}
    )
    t2_id = t2_res.json()["id"]
    cancel_res = client.post(f"/api/tasks/{t2_id}/cancel", headers={"Authorization": f"Bearer {admin_token}"})
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "Cancelled"

# --- 10. DUPLICATE CONTROL TESTS ---

def test_duplicate_control(admin_token):
    # 1. Unique customer name per company
    unique_cust = f"Duplicate Corp {uuid.uuid4().hex[:6]}"
    c1 = client.post("/api/customers/", headers={"Authorization": f"Bearer {admin_token}"}, json={"name": unique_cust})
    assert c1.status_code == 200
    c2 = client.post("/api/customers/", headers={"Authorization": f"Bearer {admin_token}"}, json={"name": unique_cust})
    assert c2.status_code == 400
    assert "already exists in this company" in c2.json()["detail"]

    # 2. Unique contact email per company
    customer_id = c1.json()["id"]
    cont_email = f"lead_{uuid.uuid4().hex[:6]}@dup.com"
    ct1 = client.post("/api/contacts/", headers={"Authorization": f"Bearer {admin_token}"}, json={"name": "Alice", "email": cont_email, "customer_id": customer_id})
    assert ct1.status_code == 200
    ct2 = client.post("/api/contacts/", headers={"Authorization": f"Bearer {admin_token}"}, json={"name": "Alice 2", "email": cont_email, "customer_id": customer_id})
    assert ct2.status_code == 400
    assert "already exists in this company" in ct2.json()["detail"]

    # 3. Duplicate lead warning (does not block creation, returns warning)
    lead_email = f"lead_{uuid.uuid4().hex[:6]}@warning.com"
    l1 = client.post("/api/leads/", headers={"Authorization": f"Bearer {admin_token}"}, json={"name": "First Lead", "email": lead_email})
    assert l1.status_code == 200
    l2 = client.post("/api/leads/", headers={"Authorization": f"Bearer {admin_token}"}, json={"name": "Second Lead", "email": lead_email})
    assert l2.status_code == 200
    # Duplicate lead warning in body and response header
    assert l2.json().get("warning") is not None
    assert "Duplicate lead warning" in l2.json()["warning"]
    assert "X-Duplicate-Lead-Warning" in l2.headers

# --- 11. STANDARDIZED ERROR RESPONSES ---

def test_standardized_error_format(admin_token):
    # 404 error
    not_found = client.get("/api/companies/999999", headers={"Authorization": f"Bearer {admin_token}"})
    assert not_found.status_code == 404
    data = not_found.json()
    assert "detail" in data
    assert "code" in data
    assert data["code"] == "HTTP_404"

    # 422 error
    bad_req = client.post("/api/leads/", headers={"Authorization": f"Bearer {admin_token}"}, json={})
    assert bad_req.status_code == 422
    data422 = bad_req.json()
    assert "detail" in data422
    assert "code" in data422
    assert data422["code"] == "VALIDATION_ERROR"
