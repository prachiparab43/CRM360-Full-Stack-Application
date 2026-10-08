import { useState, useEffect } from 'react';
import api from '../api';
import { Plus, Edit, Search } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Leads() {
  const { user } = useAuth();
  const [leads, setLeads] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [search, setSearch] = useState('');
  
  const [showModal, setShowModal] = useState(false);
  const [showDisqualify, setShowDisqualify] = useState(false);
  const [activeLead, setActiveLead] = useState(null);
  const [disqualifyReason, setDisqualifyReason] = useState('');
  const [editingId, setEditingId] = useState(null);
  
  const [formData, setFormData] = useState({ name: '', company: '', email: '', phone: '', status: 'New', assigned_employee_id: '' });

  const fetchLeads = async () => {
    try {
      const res = await api.get(`/leads/?search=${search}`);
      setLeads(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchLeads();
    api.get('/employees/').then(res => setEmployees(res.data)).catch(console.error);
  }, [search]);

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
      alert(err.response?.data?.detail || 'Error');
    }
  };

  const qualifyLead = async (id) => {
    if (!confirm('Qualify this lead and create an opportunity?')) return;
    try {
      await api.post(`/leads/${id}/qualify`);
      fetchLeads();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error qualifying');
    }
  };

  const disqualifyLead = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/leads/${activeLead.id}/disqualify`, { reason: disqualifyReason });
      setShowDisqualify(false);
      fetchLeads();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error disqualifying');
    }
  };

  const getStatusColor = (s) => {
    const colors = { 'New': 'bg-blue-100 text-blue-800', 'Qualified': 'bg-green-100 text-green-800', 'Disqualified': 'bg-red-100 text-red-800' };
    return colors[s] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Leads</h1>
        <button onClick={() => { setEditingId(null); setFormData({name:'', company:'', email:'', phone:'', status:'New', assigned_employee_id: user.id}); setShowModal(true); }} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus size={18} /> Add Lead
        </button>
      </div>

      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6 flex gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
          <input type="text" placeholder="Search leads..." className="pl-10 pr-4 py-2 w-full border rounded-lg focus:ring-2 outline-none" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-x-auto overflow-y-hidden"><table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200 text-sm font-semibold text-gray-600 uppercase">
              <th className="px-6 py-4">Name / Company</th>
              <th className="px-6 py-4">Contact</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {leads.map(l => (
              <tr key={l.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 font-medium text-gray-900">{l.name} <div className="text-xs text-gray-500 font-normal">{l.company}</div></td>
                <td className="px-6 py-4"><div className="text-sm">{l.email}</div><div className="text-sm text-gray-500">{l.phone}</div></td>
                <td className="px-6 py-4"><span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(l.status)}`}>{l.status}</span></td>
                <td className="px-6 py-4 text-right flex justify-end gap-3 items-center">
                  {l.status !== 'Qualified' && l.status !== 'Disqualified' && (
                    <>
                      <button onClick={() => qualifyLead(l.id)} className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded hover:bg-green-100">Qualify</button>
                      <button onClick={() => { setActiveLead(l); setDisqualifyReason(''); setShowDisqualify(true); }} className="text-xs bg-red-50 text-red-700 px-2 py-1 rounded hover:bg-red-100">Disqualify</button>
                    </>
                  )}
                  <button onClick={() => { setEditingId(l.id); setFormData({name: l.name, company: l.company||'', email: l.email||'', phone: l.phone||'', status: l.status, assigned_employee_id: l.assigned_employee_id||''}); setShowModal(true); }} className="text-blue-600 hover:text-blue-900"><Edit size={18} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-xl w-full max-w-md shadow-2xl">
            <h2 className="text-xl font-bold mb-4">{editingId ? 'Edit' : 'Add'} Lead</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div><label className="block text-sm font-medium mb-1">Name *</label><input required value={formData.name} onChange={e=>setFormData({...formData, name: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
              <div><label className="block text-sm font-medium mb-1">Company</label><input value={formData.company} onChange={e=>setFormData({...formData, company: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
              <div><label className="block text-sm font-medium mb-1">Email</label><input type="email" value={formData.email} onChange={e=>setFormData({...formData, email: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
              <div><label className="block text-sm font-medium mb-1">Assigned To</label>
                <select value={formData.assigned_employee_id} onChange={e=>setFormData({...formData, assigned_employee_id: e.target.value})} className="w-full p-2 border rounded outline-none">
                  <option value="">Unassigned</option>
                  {employees.map(e => <option key={e.id} value={e.id}>{e.name}</option>)}
                </select>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showDisqualify && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-xl w-full max-w-md shadow-2xl">
            <h2 className="text-xl font-bold mb-4">Disqualify Lead</h2>
            <form onSubmit={disqualifyLead} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Reason for Disqualification *</label>
                <textarea required rows="3" value={disqualifyReason} onChange={e=>setDisqualifyReason(e.target.value)} className="w-full p-2 border rounded focus:ring-2 outline-none" placeholder="Too expensive, no longer interested..."></textarea>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button type="button" onClick={() => setShowDisqualify(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">Disqualify</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


