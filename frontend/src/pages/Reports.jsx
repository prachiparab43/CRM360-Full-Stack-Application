import { useState } from 'react';
import api from '../api';
import { Download } from 'lucide-react';

export default function Reports() {
  const [stage, setStage] = useState('Won');
  const [loading, setLoading] = useState(false);

  const handleExport = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.get(`/reports/opportunities/export?stage=${stage}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `opportunities_export_${stage}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert('Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Reports & Analytics</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Opportunities Report</h2>
          <p className="text-gray-500 mb-6 text-sm">Download a detailed CSV export of all opportunities filtered by their current stage. Respects your current data visibility scope.</p>
          
          <form onSubmit={handleExport} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Opportunity Stage</label>
              <select value={stage} onChange={(e) => setStage(e.target.value)} className="w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-600 outline-none">
                <option value="">All Stages</option>
                <option value="Opportunity">Opportunity</option>
                <option value="Proposal">Proposal</option>
                <option value="Negotiation">Negotiation</option>
                <option value="Won">Won</option>
                <option value="Lost">Lost</option>
              </select>
            </div>
            <button disabled={loading} type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center justify-center gap-2 w-full hover:bg-blue-700 disabled:opacity-50">
              <Download size={18} /> {loading ? 'Generating...' : 'Export CSV'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}


