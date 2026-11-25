import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api';
import { 
  Plus, Edit, Search, ArrowRightCircle, ExternalLink, 
  CheckCircle2, AlertCircle, Building2, User, Phone, Mail, DollarSign, Calendar
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Leads() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [leads, setLeads] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  
  // Modals
  const [showModal, setShowModal] = useState(false);
  const [showDisqualify, setShowDisqualify] = useState(false);
  const [showConvertModal, setShowConvertModal] = useState(false);
  
  const [activeLead, setActiveLead] = useState(null);
  const [disqualifyReason, setDisqualifyReason] = useState('');
  const [editingId, setEditingId] = useState(null);
  
  // Lead Create/Edit Form
  const [formData, setFormData] = useState({
    name: '',
    company: '',
    contact_name: '',
    email: '',
    phone: '',
    lead_source: 'Website',
    requirement: '',
    notes: '',
    status: 'New',
    assigned_employee_id: ''
  });

  // Conversion Form
  const [convertForm, setConvertForm] = useState({
    name: '',
    expected_value: 10000,
    probability: 10,
    expected_close_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    stage: 'Opportunity',
    description: '',
    notes: '',
    assigned_employee_id: '',
    customer_id: ''
  });
  const [convertSubmitting, setConvertSubmitting] = useState(false);
  const [convertError, setConvertError] = useState('');

  const fetchLeads = async () => {
    setLoading(true);
    try {
      let url = `/leads/?search=${encodeURIComponent(search)}`;
      if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;
      const res = await api.get(url);
      const data = Array.isArray(res.data) ? res.data : (res.data?.items || []);
      setLeads(data);
    } catch (err) {
      console.error('Error fetching leads:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeads();
  }, [search, statusFilter]);

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
      if (editingId) {
        await api.put(`/leads/${editingId}`, payload);
      } else {
        await api.post('/leads/', payload);
      }
      setShowModal(false);
      fetchLeads();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error saving lead');
    }
  };

  const handleOpenConvert = (lead) => {
    setActiveLead(lead);
    setConvertError('');
    // Prepopulate deal form from lead details
    const defaultDealName = lead.company 
      ? `${lead.company} - ${lead.requirement ? lead.requirement.slice(0, 30) : 'Deal'}`
      : `${lead.name} - Opportunity`;

    // Try matching customer by company name if available
    let matchedCustomerId = '';
    if (lead.company && customers.length > 0) {
      const found = customers.find(c => c.name.toLowerCase() === lead.company.toLowerCase());
      if (found) matchedCustomerId = found.id;
    }

    setConvertForm({
      name: defaultDealName,
      expected_value: 25000,
      probability: 20,
      expected_close_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      stage: 'Opportunity',
      description: lead.requirement || '',
      notes: lead.notes || (lead.lead_source ? `Source: ${lead.lead_source}` : ''),
      assigned_employee_id: lead.assigned_employee_id || user?.id || '',
      customer_id: matchedCustomerId
    });
    setShowConvertModal(true);
  };

  const submitConversion = async (e) => {
    e.preventDefault();
    setConvertSubmitting(true);
    setConvertError('');
    try {
      const payload = {
        name: convertForm.name.trim(),
        expected_value: Number(convertForm.expected_value) || 0,
        probability: Number(convertForm.probability) || 10,
        expected_close_date: convertForm.expected_close_date || null,
        stage: convertForm.stage || 'Opportunity',
        description: convertForm.description,
        notes: convertForm.notes,
        assigned_employee_id: convertForm.assigned_employee_id ? Number(convertForm.assigned_employee_id) : null,
        customer_id: convertForm.customer_id ? Number(convertForm.customer_id) : null,
      };

      await api.post(`/leads/${activeLead.id}/convert`, payload);
      setShowConvertModal(false);
      fetchLeads();
    } catch (err) {
      console.error('Conversion failed:', err);
      setConvertError(err.response?.data?.detail || 'Conversion failed. Please verify input fields.');
    } finally {
      setConvertSubmitting(false);
    }
  };

  const markQualified = async (id) => {
    try {
      await api.put(`/leads/${id}`, { status: 'Qualified' });
      fetchLeads();
    } catch (err) {
      // If PUT doesn't allow direct status update without endpoint, use qualify
      try {
        await api.post(`/leads/${id}/qualify`, { expected_value: 0 });
        fetchLeads();
      } catch (e2) {
        alert(e2.response?.data?.detail || 'Error setting lead to Qualified');
      }
    }
  };

  const disqualifyLead = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/leads/${activeLead.id}/disqualify`, { reason: disqualifyReason });
      setShowDisqualify(false);
      fetchLeads();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error disqualifying lead');
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'New':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-50 text-blue-700 border border-blue-200">New</span>;
      case 'Contacted':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-50 text-amber-700 border border-amber-200">Contacted</span>;
      case 'Qualified':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">Qualified</span>;
      case 'Disqualified':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-rose-50 text-rose-700 border border-rose-200">Disqualified</span>;
      default:
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-gray-50 text-gray-700 border border-gray-200">{status}</span>;
    }
  };

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Lead Management</h1>
          <p className="text-gray-500 text-sm mt-0.5">Track, qualify, and convert potential clients into active opportunities.</p>
        </div>
        <button 
          onClick={() => { 
            setEditingId(null); 
            setFormData({
              name: '', company: '', contact_name: '', email: '', phone: '', 
              lead_source: 'Website', requirement: '', notes: '', status: 'New', 
              assigned_employee_id: user?.id || ''
            }); 
            setShowModal(true); 
          }} 
          className="bg-blue-600 text-white px-4 py-2.5 rounded-lg flex items-center justify-center gap-2 hover:bg-blue-700 transition shadow-sm font-medium text-sm"
        >
          <Plus size={18} /> Add New Lead
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative flex-1 w-full max-w-md">
          <Search className="absolute left-3.5 top-2.5 text-gray-400" size={18} />
          <input 
            type="text" 
            placeholder="Search leads by name or company..." 
            className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm" 
            value={search} 
            onChange={(e) => setSearch(e.target.value)} 
          />
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Status:</label>
          <select 
            value={statusFilter} 
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="New">New</option>
            <option value="Contacted">Contacted</option>
            <option value="Qualified">Qualified</option>
            <option value="Disqualified">Disqualified</option>
          </select>
        </div>
      </div>

      {/* Leads Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50/75 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                <th className="px-6 py-3.5">Lead & Company</th>
                <th className="px-6 py-3.5">Contact Details</th>
                <th className="px-6 py-3.5">Assigned To</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Linked Opportunity</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 text-sm">
              {loading ? (
                <tr>
                  <td colSpan="6" className="text-center py-8 text-gray-400">Loading leads...</td>
                </tr>
              ) : leads.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center py-12 text-gray-500">
                    No leads found matching your criteria.
                  </td>
                </tr>
              ) : (
                leads.map(l => (
                  <tr key={l.id} className="hover:bg-gray-50/80 transition">
                    {/* Lead & Company */}
                    <td className="px-6 py-4">
                      <div className="font-semibold text-gray-900">{l.name}</div>
                      {l.company && <div className="text-xs text-gray-500 flex items-center gap-1 mt-0.5"><Building2 size={12} /> {l.company}</div>}
                      {l.lead_source && <span className="inline-block mt-1 text-[11px] font-medium text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">Source: {l.lead_source}</span>}
                    </td>

                    {/* Contact Info */}
                    <td className="px-6 py-4">
                      {l.email ? <div className="text-gray-900 text-xs">{l.email}</div> : <span className="text-xs text-gray-400">No email</span>}
                      {l.phone && <div className="text-xs text-gray-500 mt-0.5">{l.phone}</div>}
                    </td>

                    {/* Assigned Employee */}
                    <td className="px-6 py-4">
                      <span className="text-gray-700 text-xs font-medium">
                        {l.assigned_employee_name || 'Unassigned'}
                      </span>
                    </td>

                    {/* Status */}
                    <td className="px-6 py-4">
                      {getStatusBadge(l.status)}
                      {l.status === 'Disqualified' && l.disqualified_reason && (
                        <p className="text-[11px] text-rose-600 mt-1 italic max-w-xs truncate" title={l.disqualified_reason}>
                          Reason: {l.disqualified_reason}
                        </p>
                      )}
                    </td>

                    {/* Linked Opportunity / Conversion Traceability */}
                    <td className="px-6 py-4">
                      {l.opportunity_id ? (
                        <div className="space-y-1">
                          <Link 
                            to="/opportunities" 
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-200 transition"
                          >
                            <ExternalLink size={12} /> Opp #{l.opportunity_id}
                          </Link>
                          {l.opportunity_name && (
                            <p className="text-[11px] text-gray-500 truncate max-w-[180px]" title={l.opportunity_name}>
                              {l.opportunity_name}
                            </p>
                          )}
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400 italic">Not Converted</span>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {/* If not yet converted and not disqualified */}
                        {!l.opportunity_id && l.status !== 'Disqualified' && (
                          <>
                            {/* If already Qualified, show prominent Convert button */}
                            {l.status === 'Qualified' ? (
                              <button
                                onClick={() => handleOpenConvert(l)}
                                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold bg-purple-600 text-white hover:bg-purple-700 transition shadow-sm"
                                title="Convert this qualified lead to an active Opportunity"
                              >
                                <ArrowRightCircle size={14} /> Convert to Opportunity
                              </button>
                            ) : (
                              /* If New or Contacted, offer Qualify and Disqualify buttons */
                              <>
                                <button
                                  onClick={() => handleOpenConvert(l)}
                                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 transition"
                                  title="Qualify and convert directly into an opportunity"
                                >
                                  Convert
                                </button>
                                <button
                                  onClick={() => { setActiveLead(l); setDisqualifyReason(''); setShowDisqualify(true); }}
                                  className="text-xs text-rose-600 hover:bg-rose-50 px-2 py-1 rounded transition"
                                >
                                  Disqualify
                                </button>
                              </>
                            )}
                          </>
                        )}

                        {/* Edit Button */}
                        <button
                          onClick={() => {
                            setEditingId(l.id);
                            setFormData({
                              name: l.name,
                              company: l.company || '',
                              contact_name: l.contact_name || '',
                              email: l.email || '',
                              phone: l.phone || '',
                              lead_source: l.lead_source || 'Website',
                              requirement: l.requirement || '',
                              notes: l.notes || '',
                              status: l.status,
                              assigned_employee_id: l.assigned_employee_id || ''
                            });
                            setShowModal(true);
                          }}
                          className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition"
                          title="Edit Lead"
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

      {/* PRIORITY 2: Convert to Opportunity Modal */}
      {showConvertModal && activeLead && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden border border-gray-100 animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-purple-700 to-indigo-700 p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs uppercase font-bold tracking-wider text-purple-200 bg-white/10 px-2.5 py-1 rounded-full">
                    Lead &rarr; Opportunity Conversion
                  </span>
                  <h2 className="text-xl font-bold mt-2">Convert "{activeLead.name}"</h2>
                  <p className="text-xs text-purple-100 mt-1">
                    Creates an active deal in the pipeline linked to this lead.
                  </p>
                </div>
                <div className="p-3 bg-white/10 rounded-xl">
                  <ArrowRightCircle size={28} />
                </div>
              </div>
            </div>

            {/* Error banner */}
            {convertError && (
              <div className="p-4 bg-red-50 border-b border-red-200 text-red-700 text-sm flex items-center gap-2">
                <AlertCircle size={18} className="shrink-0" />
                <span>{convertError}</span>
              </div>
            )}

            {/* Prepopulated Read-Only Lead Summary */}
            <div className="bg-gray-50 px-6 py-3 border-b border-gray-200 text-xs text-gray-600 grid grid-cols-2 gap-2">
              <div><span className="font-semibold text-gray-700">Company:</span> {activeLead.company || 'N/A'}</div>
              <div><span className="font-semibold text-gray-700">Contact Email:</span> {activeLead.email || 'N/A'}</div>
              <div><span className="font-semibold text-gray-700">Source:</span> {activeLead.lead_source || 'Direct'}</div>
              <div><span className="font-semibold text-gray-700">Lead ID:</span> #{activeLead.id}</div>
            </div>

            {/* Conversion Form */}
            <form onSubmit={submitConversion} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-gray-700 mb-1">
                  Opportunity / Deal Name *
                </label>
                <input
                  required
                  type="text"
                  value={convertForm.name}
                  onChange={(e) => setConvertForm({ ...convertForm, name: e.target.value })}
                  className="w-full p-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 outline-none"
                  placeholder="e.g. Acme Corp - CRM License Rollout"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">
                    Expected Monetary Value ($) *
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-2.5 text-gray-400 font-semibold">$</span>
                    <input
                      required
                      type="number"
                      min="0"
                      step="100"
                      value={convertForm.expected_value}
                      onChange={(e) => setConvertForm({ ...convertForm, expected_value: e.target.value })}
                      className="w-full pl-8 pr-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">
                    Win Probability (%) *
                  </label>
                  <input
                    required
                    type="number"
                    min="0"
                    max="100"
                    value={convertForm.probability}
                    onChange={(e) => setConvertForm({ ...convertForm, probability: e.target.value })}
                    className="w-full p-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">
                    Expected Close Date *
                  </label>
                  <input
                    required
                    type="date"
                    value={convertForm.expected_close_date}
                    onChange={(e) => setConvertForm({ ...convertForm, expected_close_date: e.target.value })}
                    className="w-full p-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">
                    Initial Pipeline Stage *
                  </label>
                  <select
                    value={convertForm.stage}
                    onChange={(e) => setConvertForm({ ...convertForm, stage: e.target.value })}
                    className="w-full p-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 outline-none bg-white"
                  >
                    <option value="Opportunity">Opportunity (Initial)</option>
                    <option value="Proposal">Proposal</option>
                    <option value="Negotiation">Negotiation</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">
                    Assigned Representative
                  </label>
                  <select
                    value={convertForm.assigned_employee_id}
                    onChange={(e) => setConvertForm({ ...convertForm, assigned_employee_id: e.target.value })}
                    className="w-full p-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 outline-none bg-white"
                  >
                    <option value="">Unassigned</option>
                    {employees.map(emp => (
                      <option key={emp.id} value={emp.id}>{emp.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">
                    Link Existing Customer (Optional)
                  </label>
                  <select
                    value={convertForm.customer_id}
                    onChange={(e) => setConvertForm({ ...convertForm, customer_id: e.target.value })}
                    className="w-full p-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 outline-none bg-white"
                  >
                    <option value="">Create / Match Later Upon Won</option>
                    {customers.map(cust => (
                      <option key={cust.id} value={cust.id}>{cust.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-gray-700 mb-1">
                  Deal Notes / Scope
                </label>
                <textarea
                  rows="2"
                  value={convertForm.notes}
                  onChange={(e) => setConvertForm({ ...convertForm, notes: e.target.value })}
                  className="w-full p-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 outline-none"
                  placeholder="Additional context from discovery call..."
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setShowConvertModal(false)}
                  className="px-4 py-2.5 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={convertSubmitting}
                  className="px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-bold shadow-md transition disabled:opacity-50"
                >
                  {convertSubmitting ? 'Converting...' : 'Complete Conversion'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add / Edit Lead Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-4">
            <h2 className="text-xl font-bold text-gray-900">{editingId ? 'Edit Lead' : 'Create New Lead'}</h2>
            <form onSubmit={handleSubmit} className="space-y-4 text-sm">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Lead Name *</label>
                  <input
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Company / Account</label>
                  <input
                    value={formData.company}
                    onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Phone</label>
                  <input
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Lead Source</label>
                  <select
                    value={formData.lead_source}
                    onChange={(e) => setFormData({ ...formData, lead_source: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white"
                  >
                    <option value="Website">Website Referral</option>
                    <option value="Conference">Conference / Event</option>
                    <option value="Partner Network">Partner Network</option>
                    <option value="Cold Call">Cold Outreach</option>
                    <option value="Inbound">Inbound Contact</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Assigned Representative</label>
                  <select
                    value={formData.assigned_employee_id}
                    onChange={(e) => setFormData({ ...formData, assigned_employee_id: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white"
                  >
                    <option value="">Unassigned</option>
                    {employees.map(e => (
                      <option key={e.id} value={e.id}>{e.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Requirement Overview</label>
                <textarea
                  rows="2"
                  value={formData.requirement}
                  onChange={(e) => setFormData({ ...formData, requirement: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="CRM requirement details..."
                />
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
                  Save Lead
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Disqualify Modal */}
      {showDisqualify && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl p-6 space-y-4">
            <h2 className="text-xl font-bold text-gray-900">Disqualify Lead</h2>
            <form onSubmit={disqualifyLead} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Reason for Disqualification *</label>
                <textarea
                  required
                  rows="3"
                  value={disqualifyReason}
                  onChange={(e) => setDisqualifyReason(e.target.value)}
                  className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-rose-500 outline-none"
                  placeholder="Budget constraints, unresponsive, no current CRM requirement..."
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowDisqualify(false)}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-semibold rounded-lg shadow-sm"
                >
                  Confirm Disqualify
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
