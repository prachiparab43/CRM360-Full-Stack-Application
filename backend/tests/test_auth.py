from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_login_success():
    response = client.post(
        "/api/auth/login",
        data={"username": "admin@crm360.com", "password": "Admin123!"}
    )
    assert response.status_code == 200, response.text
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_failure():
    response = client.post(
        "/api/auth/login",
        data={"username": "admin@crm360.com", "password": "wrongpassword"}
    )
    assert response.status_code == 400

def test_read_users_me():
    # Login first
    login_res = client.post(
        "/api/auth/login",
        data={"username": "admin@crm360.com", "password": "Admin123!"}
    )
    token = login_res.json()["access_token"]
    
    # Access protected route
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "admin@crm360.com"
    assert response.json()["name"] == "System Admin"

