import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { 
  Plus, Edit, Search, ExternalLink, Building2, User, 
  Calendar, DollarSign, ArrowRight, Eye, Sparkles, AlertCircle
} from 'lucide-react';

export default function Opportunities() {
  const [opportunities, setOpportunities] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState('');
  const [stageFilter, setStageFilter] = useState('');
  const [loading, setLoading] = useState(true);
  
  const [showModal, setShowModal] = useState(false);
  const [showLost, setShowLost] = useState(false);
  const [showDetail, setShowDetail] = useState(false);
  const [activeOpp, setActiveOpp] = useState(null);
  const [lostReason, setLostReason] = useState('');
  const [editingId, setEditingId] = useState(null);
  
  const [formData, setFormData] = useState({ 
    name: '', 
    expected_value: 0, 
    probability: 10, 
    expected_close_date: '', 
    stage: 'Opportunity', 
    customer_id: '',
    assigned_employee_id: '',
    description: '',
    notes: ''
  });

  const fetchOpps = async () => {
    setLoading(true);
    try {
      let url = `/opportunities/?search=${encodeURIComponent(search)}`;
      if (stageFilter) url += `&stage=${encodeURIComponent(stageFilter)}`;
      const res = await api.get(url);
      const data = Array.isArray(res.data) ? res.data : (res.data?.items || []);
      setOpportunities(data);
    } catch (err) {
      console.error('Error fetching opportunities:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOpps();
  }, [search, stageFilter]);

  useEffect(() => {
    api.get('/employees/').then(res => {
      const data = Array.isArray(res.data) ? res.data : (res.data?.items || []);
      setEmployees(data);
    }).catch(console.error);

    api.get('/customers/').then(res => {
      const data = Array.isArray(res.data) ? res.data : (res.data?.items || []);
      setCustomers(data);
    }).catch(console.error);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...formData };
      if (!payload.assigned_employee_id) payload.assigned_employee_id = null;
      if (!payload.customer_id) payload.customer_id = null;
      if (!payload.expected_close_date) delete payload.expected_close_date;
      
      if (editingId) {
        await api.put(`/opportunities/${editingId}`, payload);
      } else {
        await api.post('/opportunities/', payload);
      }
      setShowModal(false);
      fetchOpps();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error saving opportunity');
    }
  };

  const updateStage = async (id, stage) => {
    if (stage === 'Lost') {
      setActiveOpp(opportunities.find(o => o.id === id) || { id });
      setLostReason('');
      setShowLost(true);
      return;
    }
    
    if (stage === 'Won' && !confirm('Mark this opportunity as WON? This will automatically create or update the Customer account.')) return;
    
    try {
      await api.post(`/opportunities/${id}/stage`, { stage });
      fetchOpps();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error updating stage');
    }
  };

  const handleLost = async (e) => {
    e.preventDefault();
    if (!lostReason.trim()) {
      alert('Please provide a reason for the lost deal.');
      return;
    }
    try {
      await api.post(`/opportunities/${activeOpp.id}/stage`, { stage: 'Lost', lost_reason: lostReason.trim() });
      setShowLost(false);
      fetchOpps();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error marking lost');
    }
  };

  const getStageColor = (s) => {
    const colors = { 
      'Opportunity': 'bg-blue-100 text-blue-800 border-blue-200', 
      'Proposal': 'bg-indigo-100 text-indigo-800 border-indigo-200', 
      'Negotiation': 'bg-purple-100 text-purple-800 border-purple-200', 
      'Won': 'bg-emerald-100 text-emerald-800 border-emerald-200', 
      'Lost': 'bg-rose-100 text-rose-800 border-rose-200' 
    };
    return colors[s] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Opportunity Pipeline</h1>
          <p className="text-gray-500 text-sm mt-0.5">Manage deals across sales stages with complete lead traceability.</p>
        </div>
        <button 
          onClick={() => { 
            setEditingId(null); 
            setFormData({
              name:'', expected_value: 20000, probability: 10, 
              expected_close_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], 
              stage:'Opportunity', customer_id: '', assigned_employee_id:'', description: '', notes: ''
            }); 
            setShowModal(true); 
          }} 
          className="bg-blue-600 text-white px-4 py-2.5 rounded-lg flex items-center justify-center gap-2 hover:bg-blue-700 transition shadow-sm font-medium text-sm"
        >
          <Plus size={18} /> Add Deal
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative flex-1 w-full max-w-md">
          <Search className="absolute left-3.5 top-2.5 text-gray-400" size={18} />
          <input 
            type="text" 
            placeholder="Search deals by name..." 
            className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm" 
            value={search} 
            onChange={(e) => setSearch(e.target.value)} 
          />
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Stage:</label>
          <select 
            value={stageFilter} 
            onChange={(e) => setStageFilter(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Stages</option>
            <option value="Opportunity">Opportunity</option>
            <option value="Proposal">Proposal</option>
            <option value="Negotiation">Negotiation</option>
            <option value="Won">Won</option>
            <option value="Lost">Lost</option>
          </select>
        </div>
      </div>

      {/* Opportunities Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50/75 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                <th className="px-6 py-3.5">Deal & Account</th>
                <th className="px-6 py-3.5">Lead Traceability</th>
                <th className="px-6 py-3.5">Value & Probability</th>
                <th className="px-6 py-3.5">Stage</th>
                <th className="px-6 py-3.5">Assigned To</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 text-sm">
              {loading ? (
                <tr>
                  <td colSpan="6" className="text-center py-8 text-gray-400">Loading pipeline deals...</td>
                </tr>
              ) : opportunities.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center py-12 text-gray-500">
                    No opportunities found matching your criteria.
                  </td>
                </tr>
              ) : (
                opportunities.map(o => (
                  <tr key={o.id} className="hover:bg-gray-50/80 transition">
                    {/* Deal Name & Close Date */}
                    <td className="px-6 py-4">
                      <div className="font-semibold text-gray-900">{o.name}</div>
                      <div className="text-xs text-gray-500 mt-0.5 flex items-center gap-1.5">
                        <Calendar size={12} /> Close Date: {o.expected_close_date || 'Open'}
                      </div>
                      {o.customer_name && (
                        <span className="inline-flex items-center gap-1 mt-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-100">
                          <Building2 size={11} /> {o.customer_name}
                        </span>
                      )}
                    </td>

                    {/* Spec Traceability: Link to Original Lead */}
                    <td className="px-6 py-4">
                      {o.lead_id ? (
                        <div className="space-y-1">
                          <Link 
                            to="/leads" 
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-200 transition"
                            title={`Converted from Lead #${o.lead_id}`}
                          >
                            <Sparkles size={12} className="text-purple-600" />
                            Lead #{o.lead_id}
                          </Link>
                          {o.lead_name && (
                            <p className="text-xs text-gray-600 font-medium truncate max-w-[170px]" title={o.lead_name}>
                              {o.lead_name}
                            </p>
                          )}
                          {o.lead_company && (
                            <p className="text-[11px] text-gray-400">
                              {o.lead_company}
                            </p>
                          )}
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400 italic">Direct Opportunity</span>
                      )}
                    </td>

                    {/* Value & Probability */}
                    <td className="px-6 py-4">
                      <div className="font-bold text-gray-900">${(o.expected_value || 0).toLocaleString()}</div>
                      <div className="text-xs text-gray-500 mt-0.5">
                        {o.probability !== null && o.probability !== undefined ? o.probability : 0}% Probability
                      </div>
                    </td>

                    {/* Stage Badge & Dropdown */}
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${getStageColor(o.stage)}`}>
                        {o.stage}
                      </span>
                      {o.stage === 'Lost' && o.lost_reason && (
                        <p className="text-[11px] text-rose-600 mt-1 italic max-w-xs truncate" title={o.lost_reason}>
                          Reason: {o.lost_reason}
                        </p>
                      )}
                    </td>

                    {/* Assigned Employee */}
                    <td className="px-6 py-4">
                      <span className="text-gray-700 text-xs font-medium">
                        {o.assigned_employee_name || 'Unassigned'}
                      </span>
                    </td>

                    {/* Actions */}
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {/* Quick Stage Progression */}
                        {o.stage !== 'Won' && o.stage !== 'Lost' && (
                          <select 
                            onChange={(e) => updateStage(o.id, e.target.value)} 
                            value={o.stage} 
                            className="text-xs border border-gray-300 rounded-lg p-1.5 bg-white text-gray-700 outline-none focus:ring-1 focus:ring-blue-500 font-medium"
                          >
                            <option disabled value="">Change Stage</option>
                            <option value="Opportunity" disabled={o.stage === 'Opportunity'}>Opportunity</option>
                            <option value="Proposal" disabled={o.stage === 'Proposal'}>Proposal</option>
                            <option value="Negotiation" disabled={o.stage === 'Negotiation'}>Negotiation</option>
                            <option value="Won">Won (Close Deal)</option>
                            <option value="Lost">Lost</option>
                          </select>
                        )}

                        {/* View Details */}
                        <button
                          onClick={() => { setActiveOpp(o); setShowDetail(true); }}
                          className="p-1.5 text-gray-500 hover:text-purple-600 hover:bg-purple-50 rounded transition"
                          title="View Traceability Details"
                        >
                          <Eye size={16} />
                        </button>

                        {/* Edit Button */}
                        <button 
                          onClick={() => { 
                            setEditingId(o.id); 
                            setFormData({
                              name: o.name, 
                              expected_value: o.expected_value || 0, 
                              probability: o.probability || 0, 
                              expected_close_date: o.expected_close_date || '', 
                              stage: o.stage, 
                              customer_id: o.customer_id || '',
                              assigned_employee_id: o.assigned_employee_id || '',
                              description: o.description || '',
                              notes: o.notes || ''
                            }); 
                            setShowModal(true); 
                          }} 
                          className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition"
                          title="Edit Opportunity"
                        >
                          <Edit size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Opportunity Detail & Traceability Modal */}
      {showDetail && activeOpp && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden border border-gray-100">
            <div className="bg-gradient-to-r from-purple-700 to-indigo-700 p-6 text-white">
              <span className="text-xs uppercase font-bold tracking-wider text-purple-200 bg-white/10 px-2.5 py-1 rounded-full">
                Opportunity Details & Traceability
              </span>
              <h2 className="text-xl font-bold mt-2">{activeOpp.name}</h2>
              <p className="text-xs text-purple-100 mt-1">ID: #{activeOpp.id} &bull; Stage: {activeOpp.stage}</p>
            </div>

            <div className="p-6 space-y-4 text-sm">
              {/* Lead Traceability Box */}
              <div className="p-4 bg-purple-50 border border-purple-100 rounded-xl space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-purple-800 flex items-center gap-1.5">
                  <Sparkles size={14} /> Originating Lead Traceability
                </h4>
                {activeOpp.lead_id ? (
                  <div className="text-xs text-purple-900 space-y-1">
                    <p><span className="font-semibold">Converted from Lead:</span> #{activeOpp.lead_id} ({activeOpp.lead_name || 'Name on file'})</p>
                    {activeOpp.lead_company && <p><span className="font-semibold">Company:</span> {activeOpp.lead_company}</p>}
                    {activeOpp.lead_source && <p><span className="font-semibold">Original Source:</span> {activeOpp.lead_source}</p>}
                    {activeOpp.lead_email && <p><span className="font-semibold">Lead Contact:</span> {activeOpp.lead_email}</p>}
                  </div>
                ) : (
                  <p className="text-xs text-purple-700 italic">This opportunity was created directly without an originating lead.</p>
                )}
              </div>

              {/* Deal Metrics */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500 font-medium">Expected Value</p>
                  <p className="text-lg font-bold text-gray-900 mt-0.5">${(activeOpp.expected_value || 0).toLocaleString()}</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500 font-medium">Win Probability</p>
                  <p className="text-lg font-bold text-gray-900 mt-0.5">{activeOpp.probability || 0}%</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500 font-medium">Expected Close</p>
                  <p className="text-sm font-semibold text-gray-900 mt-0.5">{activeOpp.expected_close_date || 'Not specified'}</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500 font-medium">Assigned Representative</p>
                  <p className="text-sm font-semibold text-gray-900 mt-0.5">{activeOpp.assigned_employee_name || 'Unassigned'}</p>
                </div>
              </div>

              {activeOpp.lost_reason && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800">
                  <span className="font-bold">Reason for Loss:</span> {activeOpp.lost_reason}
                </div>
              )}

              {activeOpp.notes && (
                <div>
                  <h5 className="text-xs font-bold uppercase text-gray-500 mb-1">Notes</h5>
                  <p className="text-xs text-gray-700 bg-gray-50 p-2.5 rounded-lg border border-gray-100">{activeOpp.notes}</p>
                </div>
              )}

              <div className="flex justify-end pt-3 border-t border-gray-100">
                <button
                  onClick={() => setShowDetail(false)}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add / Edit Opportunity Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl p-6 space-y-4">
            <h2 className="text-xl font-bold text-gray-900">{editingId ? 'Edit Deal' : 'Add New Deal'}</h2>
            <form onSubmit={handleSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Deal Name *</label>
                <input 
                  required 
                  value={formData.name} 
                  onChange={e => setFormData({ ...formData, name: e.target.value })} 
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Value ($)</label>
                  <input 
                    type="number" 
                    min="0"
                    value={formData.expected_value} 
                    onChange={e => setFormData({ ...formData, expected_value: Number(e.target.value) })} 
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Probability (%)</label>
                  <input 
                    type="number" 
                    min="0"
                    max="100" 
                    value={formData.probability} 
                    onChange={e => setFormData({ ...formData, probability: Number(e.target.value) })} 
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Expected Close Date</label>
                <input 
                  type="date" 
                  value={formData.expected_close_date} 
                  onChange={e => setFormData({ ...formData, expected_close_date: e.target.value })} 
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Assigned To</label>
                  <select 
                    value={formData.assigned_employee_id} 
                    onChange={e => setFormData({ ...formData, assigned_employee_id: e.target.value })} 
                    className="w-full p-2 border border-gray-300 rounded-lg outline-none bg-white"
                  >
                    <option value="">Unassigned</option>
                    {employees.map(e => (
                      <option key={e.id} value={e.id}>{e.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Link Account</label>
                  <select 
                    value={formData.customer_id} 
                    onChange={e => setFormData({ ...formData, customer_id: e.target.value })} 
                    className="w-full p-2 border border-gray-300 rounded-lg outline-none bg-white"
                  >
                    <option value="">No Account</option>
                    {customers.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-gray-100">
                <button 
                  type="button" 
                  onClick={() => setShowModal(false)} 
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg shadow-sm"
                >
                  Save Deal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Lost Reason Modal */}
      {showLost && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl p-6 space-y-4">
            <h2 className="text-xl font-bold text-gray-900">Mark Opportunity as Lost</h2>
            <form onSubmit={handleLost} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Reason for Loss *</label>
                <textarea 
                  required 
                  rows="3" 
                  value={lostReason} 
                  onChange={e => setLostReason(e.target.value)} 
                  className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-rose-500 outline-none" 
                  placeholder="Competitor won pricing, budget canceled, client postponed project..."
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button 
                  type="button" 
                  onClick={() => setShowLost(false)} 
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-semibold rounded-lg shadow-sm"
                >
                  Confirm Lost
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
