import { useState, useEffect } from 'react';
import api from '../api';
import { useAuth } from '../context/AuthContext';
import { 
  Users, Building2, Briefcase, DollarSign, CheckCircle, Clock, 
  AlertTriangle, RefreshCw, Calendar, Activity, MapPin, UserCheck, 
  TrendingUp, ArrowUpRight, ShieldCheck, ChevronRight
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, 
  ResponsiveContainer, PieChart, Pie, Cell, Legend 
} from 'recharts';

export default function Dashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [charts, setCharts] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, chartRes] = await Promise.all([
        api.get('/dashboard/summary'),
        api.get('/dashboard/charts')
      ]);
      setSummary(sumRes.data);
      setCharts(chartRes.data);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      const detail = err.response?.data?.detail;
      const status = err.response?.status;
      if (status === 403) {
        setError(`Access Denied (403): ${detail || 'You do not have permission to view Dashboard metrics.'}`);
      } else if (status === 401) {
        setError('Authentication Expired: Please log in again to access the dashboard.');
      } else if (status === 500) {
        setError(`Server Error (500): ${detail || 'Internal server error while calculating metrics.'}`);
      } else if (err.code === 'ERR_NETWORK' || !err.response) {
        setError('Connection Error: Unable to reach the backend API at localhost:8000.');
      } else {
        setError(detail || 'Failed to load dashboard data. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-6 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/3"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-32 bg-gray-200 rounded-xl"></div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          <div className="h-80 bg-gray-200 rounded-xl"></div>
          <div className="h-80 bg-gray-200 rounded-xl"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 md:p-8 max-w-7xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center space-y-4 shadow-sm">
          <div className="inline-flex p-3 bg-red-100 rounded-full text-red-600">
            <AlertTriangle size={32} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-red-900">Dashboard Data Loading Issue</h2>
            <p className="text-red-700 mt-1 max-w-lg mx-auto">{error}</p>
          </div>
          <button
            onClick={fetchDashboardData}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition shadow-sm"
          >
            <RefreshCw size={18} /> Retry Loading
          </button>
        </div>
      </div>
    );
  }

  if (!summary || !charts) return null;

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4'];
  const STAGE_COLORS = {
    'Opportunity': 'bg-blue-100 text-blue-800 border-blue-200',
    'Proposal': 'bg-indigo-100 text-indigo-800 border-indigo-200',
    'Negotiation': 'bg-purple-100 text-purple-800 border-purple-200',
    'Won': 'bg-emerald-100 text-emerald-800 border-emerald-200',
    'Lost': 'bg-rose-100 text-rose-800 border-rose-200',
  };

  const openOpps = (summary.total_opportunities || 0) - (summary.won_opportunities || 0) - (summary.lost_opportunities || 0);

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-8 pb-16">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-gray-100 pb-5">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Executive Dashboard</h1>
          <p className="text-gray-500 mt-1">Real-time CRM metrics, sales pipeline, and field operations overview.</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-100">
            <ShieldCheck size={14} /> Scoped: {user?.role_name || 'Standard'}
          </span>
          <button
            onClick={fetchDashboardData}
            className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition shadow-sm"
          >
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {/* Primary KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Pipeline Value */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-purple-600 bg-purple-50 px-2.5 py-1 rounded-md">Pipeline Value</span>
            <div className="p-2.5 bg-purple-50 text-purple-600 rounded-lg">
              <TrendingUp size={22} />
            </div>
          </div>
          <div className="mt-4">
            <p className="text-2xl font-black text-gray-900">${(summary.pipeline_value || 0).toLocaleString()}</p>
            <p className="text-xs text-gray-500 mt-1">Across {openOpps} open deals</p>
          </div>
        </div>

        {/* Won Revenue */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-md">Won Revenue</span>
            <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-lg">
              <DollarSign size={22} />
            </div>
          </div>
          <div className="mt-4">
            <p className="text-2xl font-black text-gray-900">${(summary.total_won_revenue || 0).toLocaleString()}</p>
            <p className="text-xs text-emerald-600 font-medium mt-1">{summary.won_opportunities || 0} deals successfully closed</p>
          </div>
        </div>

        {/* Total Leads */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2.5 py-1 rounded-md">Total Leads</span>
            <div className="p-2.5 bg-blue-50 text-blue-600 rounded-lg">
              <Users size={22} />
            </div>
          </div>
          <div className="mt-4">
            <p className="text-2xl font-black text-gray-900">{summary.total_leads || 0}</p>
            <p className="text-xs text-gray-500 mt-1">{summary.qualified_leads || 0} qualified &bull; {summary.contacted_leads || 0} contacted</p>
          </div>
        </div>

        {/* Total Customers */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-600 bg-amber-50 px-2.5 py-1 rounded-md">Active Accounts</span>
            <div className="p-2.5 bg-amber-50 text-amber-600 rounded-lg">
              <Building2 size={22} />
            </div>
          </div>
          <div className="mt-4">
            <p className="text-2xl font-black text-gray-900">{summary.active_customers || summary.total_customers || 0}</p>
            <p className="text-xs text-gray-500 mt-1">Out of {summary.total_customers || 0} total accounts</p>
          </div>
        </div>
      </div>

      {/* Main Charts: Opportunity Pipeline Value & Lead Status Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Opportunity Stage Pipeline */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-gray-900">Opportunity Pipeline Value</h2>
              <p className="text-xs text-gray-500">Monetary value of opportunities grouped by stage</p>
            </div>
          </div>
          <div className="h-72">
            {charts.opportunity_distribution && charts.opportunity_distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={charts.opportunity_distribution} margin={{ top: 15, right: 15, left: 10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
                  <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: '#6b7280', fontSize: 12 }} />
                  <YAxis 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: '#6b7280', fontSize: 12 }} 
                    tickFormatter={(v) => v === 0 ? '$0' : (v >= 1000 ? `$${(v / 1000).toLocaleString()}k` : `$${v}`)} 
                  />
                  <RechartsTooltip 
                    cursor={{ fill: '#f8fafc' }} 
                    formatter={(value) => [`$${Number(value).toLocaleString()}`, 'Pipeline Value']}
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }} 
                  />
                  <Bar dataKey="value" fill="#7c3aed" radius={[6, 6, 0, 0]} maxBarSize={48} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400">No opportunities data</div>
            )}
          </div>
        </div>

        {/* Lead Status Distribution */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-gray-900">Lead Status Breakdown</h2>
              <p className="text-xs text-gray-500">Proportion of leads by qualification stage</p>
            </div>
          </div>
          <div className="h-72 flex justify-center">
            {charts.lead_distribution && charts.lead_distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={charts.lead_distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={4}
                    dataKey="value"
                    nameKey="label"
                  >
                    {charts.lead_distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip 
                    formatter={(value, name) => [`${value} Leads`, name]}
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }} 
                  />
                  <Legend iconType="circle" wrapperStyle={{ fontSize: '13px', color: '#4b5563' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400">No leads data</div>
            )}
          </div>
        </div>
      </div>

      {/* Detailed Spec Modules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Module 1: Lead Summary Details */}
        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 space-y-4">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              <Users size={18} className="text-blue-600" /> Lead Pipeline
            </h3>
            <span className="text-xs bg-gray-100 text-gray-600 font-semibold px-2 py-0.5 rounded-full">
              {summary.total_leads} Total
            </span>
          </div>
          <div className="space-y-2.5 text-sm">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">New Leads</span>
              <span className="font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">{summary.new_leads || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Contacted</span>
              <span className="font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded">{summary.contacted_leads || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Qualified</span>
              <span className="font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">{summary.qualified_leads || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Disqualified</span>
              <span className="font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded">{summary.disqualified_leads || 0}</span>
            </div>
          </div>
        </div>

        {/* Module 2: Opportunity & Stage Breakdown */}
        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 space-y-4">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              <Briefcase size={18} className="text-purple-600" /> Deals by Stage
            </h3>
            <span className="text-xs bg-gray-100 text-gray-600 font-semibold px-2 py-0.5 rounded-full">
              {summary.total_opportunities} Total
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {['Opportunity', 'Proposal', 'Negotiation', 'Won', 'Lost'].map(stage => {
              const count = summary.opportunities_by_stage?.[stage] || 0;
              const color = STAGE_COLORS[stage] || 'bg-gray-100 text-gray-800 border-gray-200';
              return (
                <div key={stage} className={`flex-1 min-w-[100px] p-2 rounded-lg border text-center ${color}`}>
                  <p className="text-xs font-semibold uppercase tracking-wider">{stage}</p>
                  <p className="text-lg font-bold mt-0.5">{count}</p>
                </div>
              );
            })}
          </div>
          <div className="pt-1 flex justify-between text-xs text-gray-500">
            <span>Expected: ${(summary.total_expected_revenue || 0).toLocaleString()}</span>
            <span>Won: ${(summary.total_won_revenue || 0).toLocaleString()}</span>
          </div>
        </div>

        {/* Module 3: Customer Accounts */}
        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 space-y-4">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              <Building2 size={18} className="text-emerald-600" /> Customer Accounts
            </h3>
            <span className="text-xs bg-gray-100 text-gray-600 font-semibold px-2 py-0.5 rounded-full">
              {summary.total_customers} Total
            </span>
          </div>
          <div className="space-y-2.5 text-sm">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Active Customers</span>
              <span className="font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">{summary.active_customers || summary.total_customers || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">New This Month</span>
              <span className="font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">{summary.new_customers || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Active Visits</span>
              <span className="font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">{summary.active_visits || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Completed Visits</span>
              <span className="font-semibold text-gray-700 bg-gray-100 px-2 py-0.5 rounded">{summary.completed_visits || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Operational Modules: Activities, Upcoming Meetings & Geo Tracking */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Activities & Tasks Feed */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 space-y-5">
          <div className="flex items-center justify-between border-b border-gray-100 pb-4">
            <div>
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <Clock size={20} className="text-amber-500" /> Tasks & Meetings
              </h2>
              <p className="text-xs text-gray-500">Upcoming schedule and task workload</p>
            </div>
            <div className="flex gap-2">
              <span className="text-xs bg-amber-50 text-amber-700 px-2 py-1 rounded-md font-semibold">
                {summary.pending_tasks || 0} Pending
              </span>
              <span className="text-xs bg-red-50 text-red-700 px-2 py-1 rounded-md font-semibold">
                {summary.overdue_tasks || 0} Overdue
              </span>
            </div>
          </div>

          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-3">Upcoming Meetings</h4>
            {summary.upcoming_meetings_list && summary.upcoming_meetings_list.length > 0 ? (
              <div className="space-y-2">
                {summary.upcoming_meetings_list.slice(0, 4).map((m, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg text-sm border border-gray-100">
                    <div className="flex items-center gap-2.5">
                      <Calendar size={16} className="text-blue-600" />
                      <div>
                        <p className="font-medium text-gray-900">{m.title || 'Client Meeting'}</p>
                        <p className="text-xs text-gray-500">
                          {m.date ? new Date(m.date).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : 'Scheduled'}
                        </p>
                      </div>
                    </div>
                    {m.participant_count ? (
                      <span className="text-xs text-gray-500">{m.participant_count} participants</span>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 bg-gray-50 rounded-lg text-center text-sm text-gray-500">
                No upcoming meetings scheduled.
              </div>
            )}
          </div>

          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-3">Recent Activities</h4>
            {summary.recent_activities && summary.recent_activities.length > 0 ? (
              <div className="space-y-2">
                {summary.recent_activities.slice(0, 4).map((act, idx) => (
                  <div key={idx} className="flex items-start gap-2.5 p-2.5 rounded-lg border border-gray-100 text-sm">
                    <Activity size={16} className="text-indigo-600 mt-0.5 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-gray-900 font-medium truncate">{act.description || `${act.type} on ${act.related_to_entity}`}</p>
                      <p className="text-xs text-gray-400">
                        {act.date ? new Date(act.date).toLocaleDateString() : 'Recent'} &bull; {act.type || 'Interaction'}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 bg-gray-50 rounded-lg text-center text-sm text-gray-500">
                No recent activity records.
              </div>
            )}
          </div>
        </div>

        {/* Geo-Tracking & Field Force Summary */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 space-y-5">
          <div className="flex items-center justify-between border-b border-gray-100 pb-4">
            <div>
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <MapPin size={20} className="text-emerald-600" /> Field Force & Geo Status
              </h2>
              <p className="text-xs text-gray-500">Live employee check-in status and field operations</p>
            </div>
            <span className="text-xs bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-md font-semibold flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              {summary.checked_in_employees || 0} Checked In
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-emerald-50/50 border border-emerald-100 rounded-lg text-center">
              <p className="text-xs font-semibold uppercase tracking-wider text-emerald-800">Checked-in Staff</p>
              <p className="text-2xl font-black text-emerald-900 mt-1">{summary.checked_in_employees || 0}</p>
            </div>
            <div className="p-4 bg-blue-50/50 border border-blue-100 rounded-lg text-center">
              <p className="text-xs font-semibold uppercase tracking-wider text-blue-800">Active Visits</p>
              <p className="text-2xl font-black text-blue-900 mt-1">{summary.active_visits || 0}</p>
            </div>
          </div>

          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-3">Staff Location Status</h4>
            {summary.employee_location_status && summary.employee_location_status.length > 0 ? (
              <div className="divide-y divide-gray-100 border border-gray-100 rounded-lg overflow-hidden">
                {summary.employee_location_status.slice(0, 5).map((emp, idx) => (
                  <div key={idx} className="p-3 flex items-center justify-between text-sm hover:bg-gray-50 transition">
                    <div className="flex items-center gap-3">
                      <div className={`w-2.5 h-2.5 rounded-full ${emp.is_checked_in ? 'bg-emerald-500' : 'bg-gray-300'}`}></div>
                      <div>
                        <p className="font-semibold text-gray-900">{emp.employee_name || `Staff #${emp.employee_id}`}</p>
                        <p className="text-xs text-gray-500">
                          {emp.check_in_time ? `Checked in: ${new Date(emp.check_in_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Not checked in today'}
                        </p>
                      </div>
                    </div>
                    {emp.latitude && emp.longitude ? (
                      <span className="text-xs text-gray-500 font-mono bg-gray-50 px-2 py-1 rounded">
                        {Number(emp.latitude).toFixed(3)}, {Number(emp.longitude).toFixed(3)}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">No GPS lock</span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 bg-gray-50 rounded-lg text-center text-sm text-gray-500">
                No active geo-tracking logs for today.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
