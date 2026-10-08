from app.db.session import SessionLocal
from app.models.domain import Employee, Company

db = SessionLocal()
admin = db.query(Employee).filter(Employee.email == "admin@crm360.local").first()
if admin:
    admin.email = "admin@crm360.com"
    db.commit()

company = db.query(Company).filter(Company.email == "admin@crm360.local").first()
if company:
    company.email = "admin@crm360.com"
    db.commit()
    
db.close()
