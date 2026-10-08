import { useState, useEffect } from 'react';
import api from '../api';
import { Plus, Edit, Search } from 'lucide-react';

export default function Customers() {
  const [customers, setCustomers] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [search, setSearch] = useState('');
  
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  
  const [formData, setFormData] = useState({ name: '', company_details: '', industry: '', address: '', phone: '', email: '', assigned_employee_id: '', status: 'Active' });

  const fetchData = async () => {
    try {
      const [custRes, empRes] = await Promise.all([
        api.get(`/customers/?search=${search}`),
        api.get('/employees/')
      ]);
      setCustomers(custRes.data);
      setEmployees(empRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => { fetchData(); }, [search]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...formData };
      if (!payload.assigned_employee_id) payload.assigned_employee_id = null;
      
      if (editingId) {
        await api.put(`/customers/${editingId}`, payload);
      } else {
        await api.post('/customers/', payload);
      }
      setShowModal(false);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error');
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Customers (Accounts)</h1>
        <button onClick={() => { setEditingId(null); setFormData({name: '', company_details: '', industry: '', address: '', phone: '', email: '', assigned_employee_id: '', status: 'Active'}); setShowModal(true); }} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus size={18} /> Add Customer
        </button>
      </div>

      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6 flex gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
          <input type="text" placeholder="Search customers..." className="pl-10 pr-4 py-2 w-full border rounded-lg focus:ring-2 outline-none" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200 text-sm font-semibold text-gray-600 uppercase">
              <th className="px-6 py-4">Account Name</th>
              <th className="px-6 py-4">Industry</th>
              <th className="px-6 py-4">Contact</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {customers.map(c => (
              <tr key={c.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 font-medium text-gray-900">{c.name}</td>
                <td className="px-6 py-4 text-gray-600">{c.industry || 'N/A'}</td>
                <td className="px-6 py-4"><div className="text-sm">{c.email}</div><div className="text-sm text-gray-500">{c.phone}</div></td>
                <td className="px-6 py-4"><span className={`px-2 py-1 text-xs rounded-full ${c.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{c.status}</span></td>
                <td className="px-6 py-4 text-right">
                  <button onClick={() => { setEditingId(c.id); setFormData({name: c.name, company_details: c.company_details||'', industry: c.industry||'', address: c.address||'', phone: c.phone||'', email: c.email||'', assigned_employee_id: c.assigned_employee_id||'', status: c.status}); setShowModal(true); }} className="text-blue-600 hover:text-blue-900"><Edit size={18} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-xl w-full max-w-md shadow-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">{editingId ? 'Edit' : 'Add'} Customer</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div><label className="block text-sm font-medium mb-1">Account Name *</label><input required value={formData.name} onChange={e=>setFormData({...formData, name: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
              <div><label className="block text-sm font-medium mb-1">Industry</label><input value={formData.industry} onChange={e=>setFormData({...formData, industry: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
              <div><label className="block text-sm font-medium mb-1">Email</label><input type="email" value={formData.email} onChange={e=>setFormData({...formData, email: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
              <div><label className="block text-sm font-medium mb-1">Phone</label><input value={formData.phone} onChange={e=>setFormData({...formData, phone: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
              <div><label className="block text-sm font-medium mb-1">Assigned To</label>
                <select value={formData.assigned_employee_id} onChange={e=>setFormData({...formData, assigned_employee_id: e.target.value})} className="w-full p-2 border rounded outline-none">
                  <option value="">Unassigned</option>
                  {employees.map(e => <option key={e.id} value={e.id}>{e.name}</option>)}
                </select>
              </div>
              <div><label className="block text-sm font-medium mb-1">Status</label>
                <select value={formData.status} onChange={e=>setFormData({...formData, status: e.target.value})} className="w-full p-2 border rounded outline-none">
                  <option>Active</option><option>Inactive</option>
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
    </div>
  );
}
