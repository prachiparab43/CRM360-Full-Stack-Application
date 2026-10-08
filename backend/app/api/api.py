from fastapi import APIRouter
from app.api.endpoints import auth, roles, companies, employees, leads, opportunities, customers, contacts, engagements, tracking, dashboard, reports

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(engagements.router_activities, prefix="/activities", tags=["activities"])
api_router.include_router(engagements.router_tasks, prefix="/tasks", tags=["tasks"])
api_router.include_router(engagements.router_meetings, prefix="/meetings", tags=["meetings"])
api_router.include_router(tracking.router_tracking, prefix="/tracking", tags=["tracking"])
api_router.include_router(tracking.router_visits, prefix="/visits", tags=["visits"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
