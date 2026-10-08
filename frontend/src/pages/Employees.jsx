import { useState, useEffect } from 'react';
import api from '../api';
import { Plus, Edit, Search } from 'lucide-react';

export default function Employees() {
  const [employees, setEmployees] = useState([]);
  const [roles, setRoles] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({ name: '', email: '', phone: '', password: '', role_id: '', company_id: '', status: 'Active' });

  const fetchData = async () => {
    try {
      const [empRes, rolRes, compRes] = await Promise.all([
        api.get(`/employees/?search=${search}`),
        api.get('/roles/'),
        api.get('/companies/')
      ]);
      setEmployees(empRes.data);
      setRoles(rolRes.data);
      setCompanies(compRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [search]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...formData };
      if (!payload.password) delete payload.password;
      
      if (editingId) {
        await api.put(`/employees/${editingId}`, payload);
      } else {
        await api.post('/employees/', payload);
      }
      setShowModal(false);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Operation failed');
    }
  };

  const openEdit = (emp) => {
    setEditingId(emp.id);
    setFormData({ name: emp.name, email: emp.email, phone: emp.phone || '', role_id: emp.role_id || '', company_id: emp.company_id || '', status: emp.status, password: '' });
    setShowModal(true);
  };

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Employees</h1>
        <button onClick={() => { setEditingId(null); setFormData({name:'', email:'', phone:'', password:'', role_id:'', company_id:'', status:'Active'}); setShowModal(true); }} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus size={18} /> Add Employee
        </button>
      </div>

      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6 flex gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
          <input type="text" placeholder="Search employees..." className="pl-10 pr-4 py-2 w-full border rounded-lg focus:ring-2 outline-none" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-x-auto overflow-y-hidden"><table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200 text-sm font-semibold text-gray-600 uppercase">
              <th className="px-6 py-4">Name</th>
              <th className="px-6 py-4">Contact</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {employees.map(e => (
              <tr key={e.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 font-medium text-gray-900">{e.name}</td>
                <td className="px-6 py-4"><div className="text-sm">{e.email}</div></td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs rounded-full ${e.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{e.status}</span>
                </td>
                <td className="px-6 py-4 text-right">
                  <button onClick={() => openEdit(e)} className="text-blue-600 hover:text-blue-900"><Edit size={18} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-xl w-full max-w-md shadow-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">{editingId ? 'Edit' : 'Add'} Employee</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div><label className="block text-sm font-medium mb-1">Name *</label><input required value={formData.name} onChange={e=>setFormData({...formData, name: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
              <div><label className="block text-sm font-medium mb-1">Email *</label><input type="email" required value={formData.email} onChange={e=>setFormData({...formData, email: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
              {!editingId && <div><label className="block text-sm font-medium mb-1">Password *</label><input type="password" required value={formData.password} onChange={e=>setFormData({...formData, password: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>}
              <div><label className="block text-sm font-medium mb-1">Role</label>
                <select value={formData.role_id} onChange={e=>setFormData({...formData, role_id: e.target.value})} className="w-full p-2 border rounded outline-none">
                  <option value="">None</option>
                  {roles.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
                </select>
              </div>
              <div><label className="block text-sm font-medium mb-1">Company</label>
                <select value={formData.company_id} onChange={e=>setFormData({...formData, company_id: e.target.value})} className="w-full p-2 border rounded outline-none">
                  <option value="">None</option>
                  {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
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


