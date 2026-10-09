import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from main import app
from app.api.deps import get_db
from app.db.session import Base
from app.models.domain import *

# Load config securely, fallback for local test
from dotenv import load_dotenv
load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "mssql+pyodbc:///?odbc_connect=Driver={ODBC Driver 18 for SQL Server};Server=localhost;Database=CRM360_Test;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;")

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def verify_test_db(url):
    if not ("_Test" in url or "_test" in url):
        print("CRITICAL: Testing against non-test database is forbidden.")
        sys.exit(1)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    verify_test_db(TEST_DATABASE_URL)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    from app.models.domain import Role, Employee
    from app.core.security import get_password_hash
    db = TestingSessionLocal()
    
    admin_role = Role(name="System Administrator", description="Full Access", status="Active")
    db.add(admin_role)
    db.commit()
    db.refresh(admin_role)
    
    admin = Employee(
        name="System Admin", 
        email="admin@crm360.com", 
        password_hash=get_password_hash("Admin123!"), 
        role_id=admin_role.id,
        status="Active"
    )
    db.add(admin)
    db.commit()
    db.close()
    
    yield
    verify_test_db(TEST_DATABASE_URL)
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
