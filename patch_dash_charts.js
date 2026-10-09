import fs from 'fs';
let content = fs.readFileSync('backend/app/api/endpoints/dashboard.py', 'utf8');

// Fix duplicate Employee join in employee performance and implement monthly sales
const newCharts = `def get_dashboard_charts(
    db: Session = Depends(deps.get_db),
    auth_info: dict = Depends(deps.PermissionChecker("Dashboard", "View"))
):
    leads_q = apply_scope(db.query(Lead.status, func.count(Lead.id)), Lead, auth_info).group_by(Lead.status).all()
    opp_q = apply_scope(db.query(Opportunity.stage, func.count(Opportunity.id)), Opportunity, auth_info).group_by(Opportunity.stage).all()
    
    perf_query = apply_scope(db.query(Employee.name, func.sum(Opportunity.expected_value)), Opportunity, auth_info).filter(Opportunity.stage == "Won")
    if 'Employee' not in str(perf_query):
        perf_query = perf_query.join(Employee, Opportunity.assigned_employee_id == Employee.id)
    emp_perf = perf_query.group_by(Employee.name).all()

    # Calculate monthly sales for the current year
    current_year = datetime.now().year
    sales_query = apply_scope(
        db.query(
            func.month(Opportunity.expected_close_date).label('month'),
            func.sum(Opportunity.expected_value).label('total')
        ), Opportunity, auth_info
    ).filter(
        Opportunity.stage == "Won",
        func.year(Opportunity.expected_close_date) == current_year
    ).group_by(func.month(Opportunity.expected_close_date)).all()
    
    # Map months to strings
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_sales_data = []
    sales_dict = {row.month: row.total for row in sales_query if row.month}
    for i in range(1, 13):
        monthly_sales_data.append(ChartDataPoint(label=months[i-1], value=sales_dict.get(i, 0)))

    return DashboardCharts(
        lead_distribution=[ChartDataPoint(label=k, value=v) for k, v in leads_q],
        opportunity_distribution=[ChartDataPoint(label=k, value=v) for k, v in opp_q],
        monthly_sales=monthly_sales_data,
        employee_performance=[ChartDataPoint(label=k, value=v or 0) for k, v in emp_perf]
    )`;

content = content.replace(/def get_dashboard_charts\([\s\S]*?return DashboardCharts\([\s\S]*?\)/, newCharts);

fs.writeFileSync('backend/app/api/endpoints/dashboard.py', content);
console.log('Dashboard charts patched');
