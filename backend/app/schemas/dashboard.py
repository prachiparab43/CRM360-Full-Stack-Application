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

class ChartDataPoint(BaseModel):
    label: str
    value: float

class DashboardCharts(BaseModel):
    lead_distribution: List[ChartDataPoint]
    opportunity_distribution: List[ChartDataPoint]
    monthly_sales: List[ChartDataPoint]
    employee_performance: List[ChartDataPoint]
