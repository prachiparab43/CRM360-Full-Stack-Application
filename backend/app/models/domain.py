from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Date, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    phone = Column(String(50))
    email = Column(String(255))
    status = Column(String(50), default="Active")
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), onupdate=func.now())

    employees = relationship("Employee", back_populates="company")

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    status = Column(String(50), default="Active")

    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="role")

class RolePermission(Base):
    __tablename__ = "role_permissions"
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    module = Column(String(100), nullable=False) # e.g. Lead, Opportunity
    action = Column(String(50), nullable=False) # e.g. View, Create, Edit, Delete
    data_scope = Column(String(50), nullable=False) # Own, Team, Company, All

    role = relationship("Role", back_populates="permissions")

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50))
    department = Column(String(100))
    designation = Column(String(100))
    role_id = Column(Integer, ForeignKey("roles.id"))
    company_id = Column(Integer, ForeignKey("companies.id"))
    password_hash = Column(String(255))
    status = Column(String(50), default="Active")
    joining_date = Column(Date)

    role = relationship("Role", back_populates="employees")
    company = relationship("Company", back_populates="employees")

class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    company = Column(String(255))
    contact_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    lead_source = Column(String(100))
    assigned_employee_id = Column(Integer, ForeignKey("employees.id"))
    status = Column(String(50), default="New") # New, Contacted, Qualified, Disqualified, Closed
    requirement = Column(Text)
    notes = Column(Text)
    disqualified_reason = Column(Text)
    created_date = Column(DateTime(timezone=True), server_default=func.now())

    assigned_employee = relationship("Employee")
    opportunity = relationship("Opportunity", back_populates="lead", uselist=False)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False) # Account / Company Name
    address = Column(Text)
    phone = Column(String(50))
    email = Column(String(255))
    industry = Column(String(100))
    assigned_employee_id = Column(Integer, ForeignKey("employees.id"))
    status = Column(String(50), default="Active")

    assigned_employee = relationship("Employee")
    contacts = relationship("Contact", back_populates="customer")

class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    expected_value = Column(Float)
    probability = Column(Float)
    expected_close_date = Column(Date)
    assigned_employee_id = Column(Integer, ForeignKey("employees.id"))
    stage = Column(String(50), default="Opportunity") # Opportunity, Proposal, Negotiation, Won, Lost
    description = Column(Text)
    notes = Column(Text)
    lost_reason = Column(Text)
    
    lead = relationship("Lead", back_populates="opportunity")
    customer = relationship("Customer")
    assigned_employee = relationship("Employee")

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    designation = Column(String(100))
    email = Column(String(255))
    phone = Column(String(50))
    alternate_phone = Column(String(50))
    status = Column(String(50), default="Active")
    notes = Column(Text)

    customer = relationship("Customer", back_populates="contacts")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(100)) # Call, Email, Visit, Note
    related_to_entity = Column(String(50)) # Lead, Opportunity, Customer, Contact
    related_to_id = Column(Integer)
    description = Column(Text)
    date = Column(DateTime(timezone=True))
    employee_id = Column(Integer, ForeignKey("employees.id"))

    employee = relationship("Employee")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    assigned_employee_id = Column(Integer, ForeignKey("employees.id"))
    related_to_entity = Column(String(50))
    related_to_id = Column(Integer)
    due_date = Column(Date)
    priority = Column(String(50))
    status = Column(String(50), default="Pending") # Pending, In Progress, Completed, Cancelled
    completion_date = Column(DateTime(timezone=True))

    assigned_employee = relationship("Employee")

class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(255), nullable=False)
    related_to_entity = Column(String(50))
    related_to_id = Column(Integer)
    date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    location = Column(String(255))
    participants = Column(Text)
    description = Column(Text)
    status = Column(String(50), default="Scheduled") # Scheduled, Completed, Cancelled, Rescheduled
    employee_id = Column(Integer, ForeignKey("employees.id"))
    employee = relationship("Employee")

class GeoTracking(Base):
    __tablename__ = "geo_tracking"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    type = Column(String(50)) # CheckIn, CheckOut, Live
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    location_info = Column(String(255))
    
    employee = relationship("Employee")

class CustomerVisit(Base):
    __tablename__ = "customer_visits"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    visit_date = Column(Date)
    check_in_time = Column(DateTime(timezone=True))
    check_out_time = Column(DateTime(timezone=True))
    location = Column(String(255))
    purpose = Column(String(255))
    remarks = Column(Text)
    status = Column(String(50), default="Scheduled")
    check_in_latitude = Column(Float)
    check_in_longitude = Column(Float)
    check_out_latitude = Column(Float)
    check_out_longitude = Column(Float)
    
    employee = relationship("Employee")
    customer = relationship("Customer")
    contact = relationship("Contact")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("employees.id"))
    action = Column(String(100))
    module = Column(String(100))
    record_id = Column(Integer)
    old_value = Column(Text)
    new_value = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    request_info = Column(Text)
