import fs from 'fs';
let text = fs.readFileSync('frontend/src/pages/Contacts.jsx', 'utf8');

text = text.replace('import { Plus, Edit, Search } from \\'lucide-react\\';', 'import { Plus, Edit, Search, Trash2 } from \\'lucide-react\\';');

const deleteFunc = `
  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this contact?')) {
      try {
        await api.delete(\`/contacts/\${id}\`);
        fetchData();
      } catch (err) {
        alert(err.response?.data?.detail || 'Error deleting contact');
      }
    }
  };
`;
text = text.replace('  const handleSubmit', deleteFunc + '\\n  const handleSubmit');

const buttonStr = '<button onClick={() => { setEditingId(c.id); setFormData({name: c.name, customer_id: c.customer_id||\'\', designation: c.designation||\'\', email: c.email||\'\', phone: c.phone||\'\', alt_phone: c.alt_phone||\'\', status: c.status}); setShowModal(true); }} className="text-blue-600 hover:text-blue-900"><Edit size={18} /></button>';

const newButtons = buttonStr + '\\n                  <button onClick={() => handleDelete(c.id)} className="text-red-600 hover:text-red-900 ml-3"><Trash2 size={18} /></button>';

text = text.replace(buttonStr, newButtons);

fs.writeFileSync('frontend/src/pages/Contacts.jsx', text);
console.log('Contacts patched');
