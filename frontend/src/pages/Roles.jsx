import { useState, useEffect } from 'react';
import api from '../api';
import { Plus, Edit } from 'lucide-react';

export default function Roles() {
  const [roles, setRoles] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({ name: '', description: '', status: 'Active', permissions: [] });

  const fetchRoles = async () => {
    try {
      const res = await api.get('/roles/');
      setRoles(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => { fetchRoles(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await api.put(`/roles/${editingId}`, formData);
      } else {
        await api.post('/roles/', formData);
      }
      setShowModal(false);
      fetchRoles();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error');
    }
  };

  const openEdit = (r) => {
    setEditingId(r.id);
    setFormData({ name: r.name, description: r.description || '', status: r.status, permissions: r.permissions || [] });
    setShowModal(true);
  };

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Roles & Permissions</h1>
        <button onClick={() => { setEditingId(null); setFormData({name:'', description:'', status:'Active', permissions:[]}); setShowModal(true); }} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus size={18} /> Add Role
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-x-auto overflow-y-hidden"><table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200 text-sm font-semibold text-gray-600 uppercase">
              <th className="px-6 py-4">Role Name</th>
              <th className="px-6 py-4">Description</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {roles.map(r => (
              <tr key={r.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 font-medium text-gray-900">{r.name}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{r.description}</td>
                <td className="px-6 py-4"><span className={`px-2 py-1 text-xs rounded-full ${r.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{r.status}</span></td>
                <td className="px-6 py-4 text-right">
                  <button onClick={() => openEdit(r)} className="text-blue-600 hover:text-blue-900"><Edit size={18} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-xl w-full max-w-3xl shadow-2xl">
            <h2 className="text-xl font-bold mb-4">{editingId ? 'Edit' : 'Add'} Role</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div><label className="block text-sm font-medium mb-1">Name *</label><input required value={formData.name} onChange={e=>setFormData({...formData, name: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
              <div><label className="block text-sm font-medium mb-1">Description</label><input value={formData.description} onChange={e=>setFormData({...formData, description: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
              <div><label className="block text-sm font-medium mb-1">Status</label>
                <select value={formData.status} onChange={e=>setFormData({...formData, status: e.target.value})} className="w-full p-2 border rounded outline-none">
                  <option>Active</option><option>Inactive</option>
                </select>
              </div>
              
              <div className="max-h-[50vh] overflow-y-auto border p-2 rounded text-sm">
                <h3 className="font-semibold mb-2 bg-gray-100 p-2 sticky top-0">Permissions</h3>
                {['Lead', 'Opportunity', 'Customer', 'Contact', 'Task', 'Meeting', 'Visit', 'Role', 'Employee', 'Company'].map(mod => (
                  <div key={mod} className="mb-4 border-b pb-2">
                    <div className="font-medium text-gray-700 mb-1">{mod}</div>
                    <div className="grid grid-cols-2 gap-2">
                      {['View', 'Edit', 'Create', 'Delete', 'Qualify Lead', 'Change Stage'].map(act => {
                        const existing = formData.permissions.find(p => p.module === mod && p.action === act);
                        return (
                          <div key={act} className="flex items-center gap-2">
                            <input 
                              type="checkbox" 
                              checked={!!existing} 
                              onChange={(e) => {
                                if(e.target.checked) {
                                  setFormData({...formData, permissions: [...formData.permissions, {module: mod, action: act, data_scope: 'Own'}]});
                                } else {
                                  setFormData({...formData, permissions: formData.permissions.filter(p => !(p.module===mod && p.action===act))});
                                }
                              }}
                            />
                            <span>{act}</span>
                            {existing && (
                              <select 
                                className="border text-xs p-1 rounded ml-auto bg-white"
                                value={existing.data_scope}
                                onChange={(e) => {
                                  const updated = formData.permissions.map(p => 
                                    (p.module===mod && p.action===act) ? {...p, data_scope: e.target.value} : p
                                  );
                                  setFormData({...formData, permissions: updated});
                                }}
                              >
                                <option value="Own">Own</option>
                                <option value="Team">Team</option>
                                <option value="Company">Company</option>
                                <option value="All">All</option>
                              </select>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                ))}
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


