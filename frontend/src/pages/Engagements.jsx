import { useState, useEffect } from 'react';
import api from '../api';
import { Plus, Edit, CheckSquare, Clock } from 'lucide-react';

export default function Engagements() {
  const [tasks, setTasks] = useState([]);
  const [meetings, setMeetings] = useState([]);
  const [employees, setEmployees] = useState([]);
  
  const [activeTab, setActiveTab] = useState('Tasks');

  const fetchData = async () => {
    try {
      const [tRes, mRes, eRes] = await Promise.all([
        api.get('/tasks/'),
        api.get('/meetings/'),
        api.get('/employees/')
      ]);
      setTasks(tRes.data);
      setMeetings(mRes.data);
      setEmployees(eRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const [taskModal, setTaskModal] = useState(false);
  const [taskData, setTaskData] = useState({ title: '', priority: 'Medium', status: 'Pending', assigned_employee_id: '', due_date: '' });

  const handleTaskSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/tasks/', taskData);
      setTaskModal(false);
      fetchData();
    } catch(err) {
      alert('Failed to save task');
    }
  };

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Tasks & Meetings</h1>
      
      <div className="flex gap-4 border-b border-gray-200 mb-6">
        <button className={`px-4 py-2 font-medium ${activeTab === 'Tasks' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`} onClick={() => setActiveTab('Tasks')}>Tasks</button>
        <button className={`px-4 py-2 font-medium ${activeTab === 'Meetings' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`} onClick={() => setActiveTab('Meetings')}>Meetings</button>
      </div>

      {activeTab === 'Tasks' && (
        <div>
          <button onClick={() => { setTaskData({title:'', priority:'Medium', status:'Pending', assigned_employee_id:'', due_date:''}); setTaskModal(true); }} className="mb-4 bg-blue-600 text-white px-4 py-2 rounded flex gap-2"><Plus size={18} /> Add Task</button>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tasks.map(t => (
              <div key={t.id} className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-bold text-gray-900">{t.title}</h3>
                  <span className={`px-2 py-1 text-xs rounded ${t.status === 'Completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>{t.status}</span>
                </div>
                <div className="text-sm text-gray-500 mb-2 flex items-center gap-1"><Clock size={14}/> Due: {t.due_date || 'N/A'}</div>
                <div className="text-sm font-medium text-gray-700">Priority: {t.priority}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'Meetings' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-bold mb-4">Upcoming Meetings</h2>
          {meetings.length === 0 ? <p className="text-gray-500">No upcoming meetings.</p> : (
            <ul className="space-y-4">
              {meetings.map(m => (
                <li key={m.id} className="border-b pb-4">
                  <div className="font-semibold">{m.title}</div>
                  <div className="text-sm text-gray-500">{m.date} | {m.start_time} - {m.end_time}</div>
                  <div className="text-sm text-gray-500">Location: {m.location}</div>
                  <div className="mt-1"><span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">{m.status}</span></div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {taskModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-xl w-full max-w-md shadow-2xl">
            <h2 className="text-xl font-bold mb-4">Add Task</h2>
            <form onSubmit={handleTaskSubmit} className="space-y-4">
              <div><label className="block text-sm font-medium mb-1">title *</label><input required value={taskData.title} onChange={e=>setTaskData({...taskData, title: e.target.value})} className="w-full p-2 border rounded" /></div>
              <div><label className="block text-sm font-medium mb-1">Due Date</label><input type="date" value={taskData.due_date} onChange={e=>setTaskData({...taskData, due_date: e.target.value})} className="w-full p-2 border rounded" /></div>
              <div><label className="block text-sm font-medium mb-1">Priority</label>
                <select value={taskData.priority} onChange={e=>setTaskData({...taskData, priority: e.target.value})} className="w-full p-2 border rounded">
                  <option>Low</option><option>Medium</option><option>High</option>
                </select>
              </div>
              <div><label className="block text-sm font-medium mb-1">Assignee</label>
                <select value={taskData.assigned_employee_id} onChange={e=>setTaskData({...taskData, assigned_employee_id: e.target.value})} className="w-full p-2 border rounded">
                  <option value="">Unassigned</option>
                  {employees.map(e => <option key={e.id} value={e.id}>{e.name}</option>)}
                </select>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button type="button" onClick={() => setTaskModal(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


