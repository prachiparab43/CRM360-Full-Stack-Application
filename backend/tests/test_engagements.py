import pytest
from fastapi.testclient import TestClient
from main import app
from app.db.session import SessionLocal
from app.models.domain import RolePermission, Role
from datetime import datetime, timedelta

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_token():
    res = client.post("/api/auth/login", data={"username": "admin@crm360.com", "password": "Admin123!"})
    return res.json()["access_token"]

@pytest.fixture(scope="module")
def setup_engagement_permissions():
    db = SessionLocal()
    role = db.query(Role).filter(Role.name == "System Administrator").first()
    perms = [
        ("Activity", ["Create", "View", "Edit", "Delete"]),
        ("Task", ["Create", "View", "Edit", "Delete"]),
        ("Meeting", ["Create", "View", "Edit", "Delete"]),
    ]
    for module, actions in perms:
        for action in actions:
            if not db.query(RolePermission).filter(RolePermission.role_id == role.id, RolePermission.action == action, RolePermission.module == module).first():
                db.add(RolePermission(role_id=role.id, module=module, action=action, data_scope="All"))
    db.commit()
    db.close()

def test_activity_crud(admin_token, setup_engagement_permissions):
    # Create
    res = client.post("/api/activities/", headers={"Authorization": f"Bearer {admin_token}"}, json={"type": "Call", "description": "Intro call"})
    assert res.status_code == 200
    assert res.json()["type"] == "Call"
    
    # Read
    res = client.get("/api/activities/", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert len(res.json()) >= 1

def test_task_crud_and_overdue(admin_token):
    # Create Overdue task
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    res = client.post("/api/tasks/", headers={"Authorization": f"Bearer {admin_token}"}, json={"title": "Follow up", "due_date": yesterday, "status": "Pending"})
    assert res.status_code == 200
    task_id = res.json()["id"]
    
    # Read Overdue
    res = client.get("/api/tasks/?overdue=true", headers={"Authorization": f"Bearer {admin_token}"})
    assert any(t["id"] == task_id for t in res.json())
    
    # Complete Task
    res = client.put(f"/api/tasks/{task_id}", headers={"Authorization": f"Bearer {admin_token}"}, json={"status": "Completed"})
    assert res.status_code == 200
    assert res.json()["status"] == "Completed"
    
    # Overdue should no longer contain it
    res = client.get("/api/tasks/?overdue=true", headers={"Authorization": f"Bearer {admin_token}"})
    assert not any(t["id"] == task_id for t in res.json())

def test_meeting_scheduling_conflict(admin_token):
    today = datetime.now().strftime("%Y-%m-%d")
    payload1 = {"subject": "Demo", "date": today, "start_time": "10:00:00", "end_time": "11:00:00", "employee_id": 1}
    res1 = client.post("/api/meetings/", headers={"Authorization": f"Bearer {admin_token}"}, json=payload1)
    assert res1.status_code == 200
    
    # Conflict
    payload2 = {"subject": "Conflict Meeting", "date": today, "start_time": "10:30:00", "end_time": "11:30:00", "employee_id": 1}
    res2 = client.post("/api/meetings/", headers={"Authorization": f"Bearer {admin_token}"}, json=payload2)
    assert res2.status_code == 400
    assert "conflict" in res2.json()["detail"].lower()
    
    # Reschedule original to fix conflict (simulate by editing)
    meeting_id = res1.json()["id"]
    res3 = client.put(f"/api/meetings/{meeting_id}", headers={"Authorization": f"Bearer {admin_token}"}, json={"start_time": "09:00:00", "end_time": "09:45:00"})
    assert res3.status_code == 200
    
    # Now payload2 should succeed
    res4 = client.post("/api/meetings/", headers={"Authorization": f"Bearer {admin_token}"}, json=payload2)
    assert res4.status_code == 200
