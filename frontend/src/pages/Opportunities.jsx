import { useState, useEffect } from 'react';
import api from '../api';
import { Plus, Edit, Search } from 'lucide-react';

export default function Opportunities() {
  const [opportunities, setOpportunities] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [search, setSearch] = useState('');
  
  const [showModal, setShowModal] = useState(false);
  const [showLost, setShowLost] = useState(false);
  const [activeOpp, setActiveOpp] = useState(null);
  const [lostReason, setLostReason] = useState('');
  const [editingId, setEditingId] = useState(null);
  
  const [formData, setFormData] = useState({ name: '', expected_value: 0, probability: 0, expected_close_date: '', stage: 'Opportunity', assigned_employee_id: '' });

  const fetchOpps = async () => {
    try {
      const res = await api.get(`/opportunities/?search=${search}`);
      setOpportunities(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchOpps();
    api.get('/employees/').then(res => setEmployees(res.data)).catch(console.error);
  }, [search]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...formData };
      if (!payload.assigned_employee_id) payload.assigned_employee_id = null;
      if (!payload.expected_close_date) delete payload.expected_close_date;
      
      if (editingId) {
        await api.put(`/opportunities/${editingId}`, payload);
      } else {
        await api.post('/opportunities/', payload);
      }
      setShowModal(false);
      fetchOpps();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error');
    }
  };

  const updateStage = async (id, stage) => {
    if (stage === 'Lost') {
      setActiveOpp({id});
      setLostReason('');
      setShowLost(true);
      return;
    }
    
    if (stage === 'Won' && !confirm('Mark this opportunity as WON and convert customer?')) return;
    
    try {
      await api.post(`/opportunities/${id}/stage`, { stage });
      fetchOpps();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error updating stage');
    }
  };

  const handleLost = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/opportunities/${activeOpp.id}/stage`, { stage: 'Lost', lost_reason: lostReason });
      setShowLost(false);
      fetchOpps();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error marking lost');
    }
  };

  const getStageColor = (s) => {
    const colors = { 'Opportunity': 'bg-blue-100 text-blue-800', 'Proposal': 'bg-indigo-100 text-indigo-800', 'Negotiation': 'bg-purple-100 text-purple-800', 'Won': 'bg-emerald-100 text-emerald-800', 'Lost': 'bg-red-100 text-red-800' };
    return colors[s] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Opportunities</h1>
        <button onClick={() => { setEditingId(null); setFormData({name:'', expected_value:0, probability:0, expected_close_date:'', stage:'Opportunity', assigned_employee_id:''}); setShowModal(true); }} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus size={18} /> Add Opportunity
        </button>
      </div>

      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6 flex gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
          <input type="text" placeholder="Search opportunities..." className="pl-10 pr-4 py-2 w-full border rounded-lg focus:ring-2 outline-none" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200 text-sm font-semibold text-gray-600 uppercase">
              <th className="px-6 py-4">Deal Name</th>
              <th className="px-6 py-4">Value</th>
              <th className="px-6 py-4">Stage</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {opportunities.map(o => (
              <tr key={o.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 font-medium text-gray-900">{o.name} <div className="text-xs text-gray-500 font-normal">Close Date: {o.expected_close_date ? o.expected_close_date : 'Not Set'}</div></td>
                <td className="px-6 py-4 font-medium text-gray-700">${(o.expected_value || 0).toLocaleString()} <div className="text-xs text-gray-500 font-normal">{o.probability !== null && o.probability !== undefined ? o.probability : 0}% Probability</div></td>
                <td className="px-6 py-4"><span className={`px-2 py-1 text-xs rounded-full ${getStageColor(o.stage)}`}>{o.stage}</span></td>
                <td className="px-6 py-4 text-right flex justify-end gap-2 items-center">
                  {o.stage !== 'Won' && o.stage !== 'Lost' && (
                    <select onChange={(e) => updateStage(o.id, e.target.value)} value={o.stage} className="text-xs border rounded p-1">
                      <option disabled>Change Stage</option>
                      {['Opportunity', 'Proposal', 'Negotiation', 'Won', 'Lost'].map(s => (
                        <option key={s} value={s} disabled={s === o.stage}>{s}</option>
                      ))}
                    </select>
                  )}
                  <button onClick={() => { setEditingId(o.id); setFormData({name: o.name, expected_value: o.expected_value||0, probability: o.probability||0, expected_close_date: o.expected_close_date||'', stage: o.stage, assigned_employee_id: o.assigned_employee_id||''}); setShowModal(true); }} className="text-blue-600 hover:text-blue-900 ml-2"><Edit size={18} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-xl w-full max-w-md shadow-2xl">
            <h2 className="text-xl font-bold mb-4">{editingId ? 'Edit' : 'Add'} Opportunity</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div><label className="block text-sm font-medium mb-1">Deal Name *</label><input required value={formData.name} onChange={e=>setFormData({...formData, name: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
              <div className="flex gap-4">
                <div className="flex-1"><label className="block text-sm font-medium mb-1">Value ($)</label><input type="number" value={formData.expected_value} onChange={e=>setFormData({...formData, expected_value: Number(e.target.value)})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
                <div className="flex-1"><label className="block text-sm font-medium mb-1">Probability (%)</label><input type="number" max="100" value={formData.probability} onChange={e=>setFormData({...formData, probability: Number(e.target.value)})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
              </div>
              <div><label className="block text-sm font-medium mb-1">Close Date</label><input type="date" value={formData.expected_close_date} onChange={e=>setFormData({...formData, expected_close_date: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
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

      {showLost && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-xl w-full max-w-md shadow-2xl">
            <h2 className="text-xl font-bold mb-4">Mark Opportunity as Lost</h2>
            <form onSubmit={handleLost} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Reason for Loss *</label>
                <textarea required rows="3" value={lostReason} onChange={e=>setLostReason(e.target.value)} className="w-full p-2 border rounded focus:ring-2 outline-none" placeholder="Competitor won, budget constraints..."></textarea>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button type="button" onClick={() => setShowLost(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">Submit</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
