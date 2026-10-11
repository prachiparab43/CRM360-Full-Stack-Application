import { useState, useEffect } from 'react';
import api from '../api';
import { Plus, Edit, CheckSquare, Clock, Calendar, CalendarCheck, MapPin, AlertCircle, User } from 'lucide-react';

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
    <div className="p-4 md:p-8 max-w-7xl mx-auto w-full">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">Tasks &amp; Meetings</h1>
        <p className="text-sm text-gray-500 mt-1">Manage team commitments, schedules, and deliverables.</p>
      </div>
      
      <div className="flex gap-4 border-b border-gray-200 mb-6">
        <button 
          className={`px-4 py-2.5 font-semibold text-sm transition-colors border-b-2 cursor-pointer flex items-center gap-2 ${
            activeTab === 'Tasks' 
              ? 'text-blue-600 border-blue-600' 
              : 'text-gray-500 border-transparent hover:text-gray-700'
          }`} 
          onClick={() => setActiveTab('Tasks')}
        >
          <CheckSquare size={16} />
          <span>Tasks ({tasks.length})</span>
        </button>
        <button 
          className={`px-4 py-2.5 font-semibold text-sm transition-colors border-b-2 cursor-pointer flex items-center gap-2 ${
            activeTab === 'Meetings' 
              ? 'text-blue-600 border-blue-600' 
              : 'text-gray-500 border-transparent hover:text-gray-700'
          }`} 
          onClick={() => setActiveTab('Meetings')}
        >
          <CalendarCheck size={16} />
          <span>Meetings ({meetings.length})</span>
        </button>
      </div>

      {activeTab === 'Tasks' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <p className="text-xs sm:text-sm text-gray-500">Track and prioritize operational team tasks.</p>
            <button 
              onClick={() => { setTaskData({title:'', priority:'Medium', status:'Pending', assigned_employee_id:'', due_date:''}); setTaskModal(true); }} 
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium text-sm flex items-center gap-2 shadow-xs transition-colors cursor-pointer"
            >
              <Plus size={18} /> Add Task
            </button>
          </div>

          {tasks.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200/90 p-12 text-center text-gray-500 shadow-2xs">
              <CheckSquare size={36} className="mx-auto text-gray-400 mb-3" />
              <p className="font-semibold text-gray-700">No tasks found</p>
              <p className="text-xs text-gray-400 mt-1">Click "Add Task" to create a new task.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5 min-w-0">
              {tasks.map(t => {
                const assignedEmp = employees.find(e => e.id === t.assigned_employee_id);
                const isOverdue = t.due_date && new Date(t.due_date) < new Date() && t.status !== 'Completed';

                return (
                  <div key={t.id} className="bg-white p-5 rounded-xl shadow-xs border border-gray-200/90 hover:shadow-md transition-shadow flex flex-col justify-between min-w-0">
                    <div>
                      <div className="flex justify-between items-start gap-2 mb-3">
                        <h3 className="font-bold text-gray-900 text-base break-words flex-1 min-w-0" title={t.title}>
                          {t.title}
                        </h3>
                        <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full shrink-0 ${
                          t.status === 'Completed' 
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                            : 'bg-amber-50 text-amber-700 border border-amber-200'
                        }`}>
                          {t.status}
                        </span>
                      </div>

                      <div className="space-y-2 text-xs text-gray-600 mb-4">
                        <div className={`flex items-center gap-2 ${isOverdue ? 'text-rose-600 font-semibold' : 'text-gray-500'}`}>
                          <Clock size={14} className="shrink-0" />
                          <span>Due: {t.due_date || 'No due date'} {isOverdue && '(Overdue)'}</span>
                        </div>

                        {assignedEmp && (
                          <div className="flex items-center gap-2 text-gray-500 truncate">
                            <User size={14} className="shrink-0 text-gray-400" />
                            <span className="truncate">Assigned: {assignedEmp.name}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
                      <span className="text-gray-400 font-medium">Priority</span>
                      <span className={`font-semibold px-2 py-0.5 rounded text-[11px] ${
                        t.priority === 'High' ? 'bg-rose-50 text-rose-700' :
                        t.priority === 'Medium' ? 'bg-amber-50 text-amber-700' :
                        'bg-slate-100 text-slate-700'
                      }`}>
                        {t.priority}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {activeTab === 'Meetings' && (
        <div className="space-y-6">
          <div>
            <p className="text-xs sm:text-sm text-gray-500">Upcoming calendar meetings and customer conferences.</p>
          </div>

          {meetings.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200/90 p-12 text-center text-gray-500 shadow-2xs">
              <CalendarCheck size={36} className="mx-auto text-gray-400 mb-3" />
              <p className="font-semibold text-gray-700">No upcoming meetings</p>
              <p className="text-xs text-gray-400 mt-1">Meetings scheduled across customer and lead engagements appear here.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5 min-w-0">
              {meetings.map(m => (
                <div key={m.id} className="bg-white p-5 rounded-xl shadow-xs border border-gray-200/90 hover:shadow-md transition-shadow flex flex-col justify-between min-w-0">
                  <div>
                    <div className="flex justify-between items-start gap-2 mb-3">
                      <h3 className="font-bold text-gray-900 text-base break-words flex-1 min-w-0" title={m.title}>
                        {m.title}
                      </h3>
                      <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full shrink-0 ${
                        m.status === 'Completed' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                        m.status === 'Cancelled' ? 'bg-rose-50 text-rose-700 border border-rose-200' :
                        'bg-blue-50 text-blue-700 border border-blue-200'
                      }`}>
                        {m.status}
                      </span>
                    </div>

                    <div className="space-y-2 text-xs text-gray-600 mb-4">
                      <div className="flex items-center gap-2 text-gray-500">
                        <Calendar size={14} className="shrink-0 text-gray-400" />
                        <span>{m.date || 'No date set'}</span>
                      </div>
                      <div className="flex items-center gap-2 text-gray-500">
                        <Clock size={14} className="shrink-0 text-gray-400" />
                        <span>{m.start_time || 'N/A'} - {m.end_time || 'N/A'}</span>
                      </div>
                      {m.location && (
                        <div className="flex items-center gap-2 text-gray-500 truncate">
                          <MapPin size={14} className="shrink-0 text-gray-400" />
                          <span className="truncate">{m.location}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
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


