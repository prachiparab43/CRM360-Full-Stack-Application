import pytest
from fastapi.testclient import TestClient
from main import app
from app.db.session import SessionLocal
from app.models.domain import RolePermission, Role

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_token():
    res = client.post("/api/auth/login", data={"username": "admin@crm360.com", "password": "Admin123!"})
    return res.json()["access_token"]

@pytest.fixture(scope="module")
def setup_dashboard_permissions():
    db = SessionLocal()
    role = db.query(Role).filter(Role.name == "System Administrator").first()
    perms = [
        ("Dashboard", ["View"]),
        ("Report", ["Export"])
    ]
    for module, actions in perms:
        for action in actions:
            if not db.query(RolePermission).filter(RolePermission.role_id == role.id, RolePermission.action == action, RolePermission.module == module).first():
                db.add(RolePermission(role_id=role.id, module=module, action=action, data_scope="All"))
    db.commit()
    db.close()

def test_dashboard_summary(admin_token, setup_dashboard_permissions):
    res = client.get("/api/dashboard/summary", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "total_opportunities" in data
    assert "total_won_revenue" in data
    # Revenue should be >= 0
    assert data["total_won_revenue"] >= 0

def test_dashboard_charts(admin_token):
    res = client.get("/api/dashboard/charts", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data["opportunity_distribution"], list)

def test_csv_export(admin_token):
    res = client.get("/api/reports/opportunities/export?stage=Won", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.headers["content-type"] == "text/csv; charset=utf-8"
    content = res.content.decode("utf-8")
    assert "Expected Value" in content
