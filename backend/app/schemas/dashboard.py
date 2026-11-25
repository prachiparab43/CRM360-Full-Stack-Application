from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class DashboardSummary(BaseModel):
    total_leads: int
    total_customers: int
    total_opportunities: int
    total_employees: int
    active_employees: int
    inactive_employees: int
    qualified_leads: int
    disqualified_leads: int
    won_opportunities: int
    lost_opportunities: int
    total_expected_revenue: float
    total_won_revenue: float
    pending_tasks: int
    completed_tasks: int
    overdue_tasks: int
    upcoming_meetings: int
    completed_visits: int

    # CRM 360 spec alignment fields
    pipeline_value: float = 0.0
    opportunities_by_stage: Dict[str, int] = {}
    new_leads: int = 0
    contacted_leads: int = 0
    new_customers: int = 0
    active_customers: int = 0
    checked_in_employees: int = 0
    active_visits: int = 0
    upcoming_meetings_list: List[Dict[str, Any]] = []
    recent_activities: List[Dict[str, Any]] = []
    employee_location_status: List[Dict[str, Any]] = []

class ChartDataPoint(BaseModel):
    label: str
    value: float

class DashboardCharts(BaseModel):
    lead_distribution: List[ChartDataPoint]
    opportunity_distribution: List[ChartDataPoint]
    monthly_sales: List[ChartDataPoint]
    employee_performance: List[ChartDataPoint]
