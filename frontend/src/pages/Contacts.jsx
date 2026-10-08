import { useState, useEffect } from 'react';
import api from '../api';
import { Plus, Edit, Search } from 'lucide-react';

export default function Contacts() {
  const [contacts, setContacts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState('');
  
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  
  const [formData, setFormData] = useState({ name: '', customer_id: '', designation: '', email: '', phone: '', alt_phone: '', status: 'Active' });

  const fetchData = async () => {
    try {
      const [contRes, custRes] = await Promise.all([
        api.get(`/contacts/?search=${search}`),
        api.get('/customers/')
      ]);
      setContacts(contRes.data);
      setCustomers(custRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => { fetchData(); }, [search]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await api.put(`/contacts/${editingId}`, formData);
      } else {
        await api.post('/contacts/', formData);
      }
      setShowModal(false);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error saving contact');
    }
  };

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Contacts</h1>
        <button onClick={() => { setEditingId(null); setFormData({name: '', customer_id: '', designation: '', email: '', phone: '', alt_phone: '', status: 'Active'}); setShowModal(true); }} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus size={18} /> Add Contact
        </button>
      </div>

      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6 flex gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
          <input type="text" placeholder="Search contacts..." className="pl-10 pr-4 py-2 w-full border rounded-lg focus:ring-2 outline-none" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-x-auto overflow-y-hidden"><table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200 text-sm font-semibold text-gray-600 uppercase">
              <th className="px-6 py-4">Name / Role</th>
              <th className="px-6 py-4">Associated Account</th>
              <th className="px-6 py-4">Contact Details</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {contacts.length === 0 ? (
              <tr>
                <td colSpan="4" className="px-6 py-8 text-center text-gray-500">
                  No contacts found. Create a new contact to get started.
                </td>
              </tr>
            ) : (
              contacts.map(c => {
                const account = customers.find(cust => cust.id === c.customer_id);
                return (
                  <tr key={c.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium text-gray-900">{c.name} <div className="text-xs text-gray-500 font-normal">{c.designation}</div></td>
                    <td className="px-6 py-4 text-gray-700">{account ? account.name : 'Unlinked'}</td>
                    <td className="px-6 py-4"><div className="text-sm">{c.email}</div><div className="text-sm text-gray-500">{c.phone}</div></td>
                    <td className="px-6 py-4 text-right">
                      <button onClick={() => { setEditingId(c.id); setFormData({name: c.name, customer_id: c.customer_id||'', designation: c.designation||'', email: c.email||'', phone: c.phone||'', alt_phone: c.alt_phone||'', status: c.status}); setShowModal(true); }} className="text-blue-600 hover:text-blue-900"><Edit size={18} /></button>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-xl w-full max-w-md shadow-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">{editingId ? 'Edit' : 'Add'} Contact</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div><label className="block text-sm font-medium mb-1">Name *</label><input required value={formData.name} onChange={e=>setFormData({...formData, name: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
              <div><label className="block text-sm font-medium mb-1">Customer Account *</label>
                <select required value={formData.customer_id} onChange={e=>setFormData({...formData, customer_id: e.target.value})} className="w-full p-2 border rounded outline-none">
                  <option value="">Select Account</option>
                  {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div><label className="block text-sm font-medium mb-1">Designation</label><input value={formData.designation} onChange={e=>setFormData({...formData, designation: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
              <div><label className="block text-sm font-medium mb-1">Email</label><input type="email" value={formData.email} onChange={e=>setFormData({...formData, email: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
              <div><label className="block text-sm font-medium mb-1">Phone</label><input value={formData.phone} onChange={e=>setFormData({...formData, phone: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none" /></div>
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


