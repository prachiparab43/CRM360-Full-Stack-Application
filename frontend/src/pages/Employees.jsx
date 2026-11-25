import { useState, useEffect } from 'react';
import api from '../api';
import { useAuth } from '../context/AuthContext';
import { 
  Plus, Edit, Search, Shield, ShieldCheck, KeyRound, 
  CheckCircle2, XCircle, Eye, UserPlus, Building2, Mail, 
  Phone, Lock, RefreshCw, AlertTriangle, UserCheck, UserX,
  Filter, ArrowUpDown, ChevronRight
} from 'lucide-react';

export default function Employees() {
  const { user } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [roles, setRoles] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [roleFilter, setRoleFilter] = useState('');

  // Modals state
  const [showModal, setShowModal] = useState(false);
  const [showAdminModal, setShowAdminModal] = useState(false);
  const [showResetModal, setShowResetModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [activeEmployee, setActiveEmployee] = useState(null);

  const [editingId, setEditingId] = useState(null);
  const [formError, setFormError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // Standard User Form Data
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    department: 'Sales',
    designation: '',
    password: '',
    confirm_password: '',
    role_id: '',
    company_id: '',
    status: 'Active'
  });

  // Dedicated Create Administrator Form Data
  const [adminFormData, setAdminFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirm_password: '',
    company_id: '',
  });

  // Reset Password Form Data
  const [resetFormData, setResetFormData] = useState({
    password: '',
    confirm_password: ''
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      let empUrl = `/employees/?search=${encodeURIComponent(search)}`;
      if (statusFilter) empUrl += `&status=${encodeURIComponent(statusFilter)}`;
      if (roleFilter) empUrl += `&role_id=${encodeURIComponent(roleFilter)}`;

      const [empRes, rolRes, compRes] = await Promise.all([
        api.get(empUrl),
        api.get('/roles/'),
        api.get('/companies/')
      ]);

      const empData = Array.isArray(empRes.data) ? empRes.data : (empRes.data?.items || []);
      const rolData = Array.isArray(rolRes.data) ? rolRes.data : (rolRes.data?.items || []);
      const compData = Array.isArray(compRes.data) ? compRes.data : (compRes.data?.items || []);

      setEmployees(empData);
      setRoles(rolData);
      setCompanies(compData);
    } catch (err) {
      console.error('Failed to load user management data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [search, statusFilter, roleFilter]);

  // Find the System Administrator role id
  const systemAdminRole = roles.find(r => r.name === 'System Administrator' || r.is_system);

  // Handlers
  const handleCreateAdmin = async (e) => {
    e.preventDefault();
    setFormError('');
    if (adminFormData.password !== adminFormData.confirm_password) {
      setFormError('Passwords do not match.');
      return;
    }
    if (adminFormData.password.length < 8) {
      setFormError('Password must be at least 8 characters long.');
      return;
    }
    if (!systemAdminRole) {
      setFormError('System Administrator role could not be resolved from the database.');
      return;
    }

    setActionLoading(true);
    try {
      const payload = {
        name: adminFormData.name.trim(),
        email: adminFormData.email.toLowerCase().trim(),
        password: adminFormData.password,
        confirm_password: adminFormData.confirm_password,
        role_id: systemAdminRole.id,
        status: 'Active',
        department: 'Executive / IT',
        designation: 'System Administrator',
        company_id: adminFormData.company_id ? parseInt(adminFormData.company_id, 10) : (user?.company_id || (companies[0]?.id || null))
      };

      await api.post('/employees/', payload);
      setShowAdminModal(false);
      setAdminFormData({ name: '', email: '', password: '', confirm_password: '', company_id: '' });
      fetchData();
    } catch (err) {
      console.error(err);
      setFormError(err.response?.data?.detail || 'Failed to create System Administrator.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStandardSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    if (!editingId && formData.password !== formData.confirm_password) {
      setFormError('Passwords do not match.');
      return;
    }

    setActionLoading(true);
    try {
      const payload = {
        name: formData.name.trim(),
        email: formData.email.toLowerCase().trim(),
        phone: formData.phone?.trim() || null,
        department: formData.department || null,
        designation: formData.designation || null,
        status: formData.status || 'Active',
        role_id: formData.role_id ? parseInt(formData.role_id, 10) : null,
        company_id: formData.company_id ? parseInt(formData.company_id, 10) : null,
      };

      if (!editingId) {
        payload.password = formData.password;
        payload.confirm_password = formData.confirm_password;
        await api.post('/employees/', payload);
      } else {
        if (formData.password) {
          payload.password = formData.password;
        }
        await api.put(`/employees/${editingId}`, payload);
      }

      setShowModal(false);
      fetchData();
    } catch (err) {
      console.error(err);
      setFormError(err.response?.data?.detail || 'Operation failed.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setFormError('');
    if (resetFormData.password !== resetFormData.confirm_password) {
      setFormError('Passwords do not match.');
      return;
    }
    if (resetFormData.password.length < 8) {
      setFormError('Password must be at least 8 characters long.');
      return;
    }

    setActionLoading(true);
    try {
      await api.post(`/employees/${activeEmployee.id}/reset-password`, {
        password: resetFormData.password,
        confirm_password: resetFormData.confirm_password
      });
      setShowResetModal(false);
      setResetFormData({ password: '', confirm_password: '' });
      alert(`Password for ${activeEmployee.email} has been successfully updated.`);
    } catch (err) {
      console.error(err);
      setFormError(err.response?.data?.detail || 'Failed to reset password.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStatusToggle = async (emp) => {
    const isActivating = emp.status !== 'Active';
    const actionVerb = isActivating ? 'activate' : 'deactivate';
    if (!confirm(`Are you sure you want to ${actionVerb} account for ${emp.name} (${emp.email})?`)) {
      return;
    }

    try {
      if (isActivating) {
        await api.post(`/employees/${emp.id}/activate`);
      } else {
        await api.post(`/employees/${emp.id}/deactivate`);
      }
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || `Failed to ${actionVerb} user.`);
    }
  };

  // Quick stats
  const totalUsers = employees.length;
  const activeUsers = employees.filter(e => e.status === 'Active').length;
  const pendingUsers = employees.filter(e => e.status === 'Pending_Approval').length;
  const adminUsers = employees.filter(e => e.role_name === 'System Administrator' || (systemAdminRole && e.role_id === systemAdminRole.id)).length;

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-6 pb-16">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight flex items-center gap-2.5">
            <ShieldCheck size={28} className="text-blue-600" /> User &amp; Access Management
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Manage system administrators, employee permissions, account approvals, and security credentials.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {/* Create System Administrator Button */}
          <button 
            onClick={() => {
              setFormError('');
              setAdminFormData({
                name: '',
                email: '',
                password: '',
                confirm_password: '',
                company_id: companies[0]?.id || ''
              });
              setShowAdminModal(true);
            }} 
            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 font-bold text-sm transition shadow-sm"
          >
            <Shield size={18} /> Create Administrator
          </button>

          {/* Add Standard User Button */}
          <button 
            onClick={() => {
              setEditingId(null);
              setFormError('');
              setFormData({
                name: '', email: '', phone: '', department: 'Sales', designation: 'Representative',
                password: '', confirm_password: '', role_id: '', company_id: user?.company_id || (companies[0]?.id || ''), status: 'Active'
              });
              setShowModal(true);
            }} 
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 font-medium text-sm transition shadow-sm"
          >
            <UserPlus size={18} /> Add User
          </button>
        </div>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Total Accounts</p>
          <p className="text-2xl font-black text-gray-900 mt-1">{totalUsers}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
          <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wider">Active Users</p>
          <p className="text-2xl font-black text-emerald-700 mt-1">{activeUsers}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
          <p className="text-xs font-semibold text-amber-600 uppercase tracking-wider">Pending Approval</p>
          <p className="text-2xl font-black text-amber-700 mt-1">{pendingUsers}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
          <p className="text-xs font-semibold text-purple-600 uppercase tracking-wider">System Administrators</p>
          <p className="text-2xl font-black text-purple-700 mt-1">{adminUsers}</p>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="bg-white p-4 rounded-xl shadow-xs border border-gray-200 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative flex-1 w-full max-w-md">
          <Search className="absolute left-3.5 top-2.5 text-gray-400" size={18} />
          <input 
            type="text" 
            placeholder="Search by name or email..." 
            className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm" 
            value={search} 
            onChange={(e) => setSearch(e.target.value)} 
          />
        </div>
        
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Role Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-gray-500 uppercase">Role:</span>
            <select 
              value={roleFilter} 
              onChange={(e) => setRoleFilter(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Roles</option>
              {roles.map(r => (
                <option key={r.id} value={r.id}>{r.name}</option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-gray-500 uppercase">Status:</span>
            <select 
              value={statusFilter} 
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="Active">Active</option>
              <option value="Pending_Approval">Pending Approval</option>
              <option value="Inactive">Inactive</option>
            </select>
          </div>
        </div>
      </div>

      {/* Users & Administrators Table */}
      <div className="bg-white rounded-xl shadow-xs border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="bg-gray-50/75 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                <th className="px-6 py-3.5">User &amp; Contact</th>
                <th className="px-6 py-3.5">Assigned Role</th>
                <th className="px-6 py-3.5">Company Workspace</th>
                <th className="px-6 py-3.5">Account Status</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-gray-400">
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-5 h-5 border-2 border-blue-600/20 border-t-blue-600 rounded-full animate-spin" />
                      <span>Loading accounts...</span>
                    </div>
                  </td>
                </tr>
              ) : employees.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-gray-500 text-sm">
                    No users found matching your filters.
                  </td>
                </tr>
              ) : (
                employees.map(e => {
                  const isAdmin = e.role_name === 'System Administrator' || (systemAdminRole && e.role_id === systemAdminRole.id);
                  return (
                    <tr key={e.id} className="hover:bg-gray-50/80 transition">
                      {/* Name & Email */}
                      <td className="px-6 py-4">
                        <div className="font-semibold text-gray-900 flex items-center gap-2">
                          {e.name}
                          {isAdmin && (
                            <span className="p-0.5 bg-purple-100 text-purple-700 rounded" title="System Administrator">
                              <Shield size={14} />
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500 mt-0.5">{e.email}</div>
                        {e.phone && <div className="text-xs text-gray-400">{e.phone}</div>}
                      </td>

                      {/* Role */}
                      <td className="px-6 py-4">
                        {e.role_name ? (
                          <span className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full border ${
                            isAdmin 
                              ? 'bg-purple-50 text-purple-700 border-purple-200' 
                              : 'bg-blue-50 text-blue-700 border-blue-200'
                          }`}>
                            {isAdmin && <Shield size={11} />}
                            {e.role_name}
                          </span>
                        ) : (
                          <span className="text-xs text-gray-400 italic">No Role Assigned</span>
                        )}
                        {isAdmin && (
                          <div className="text-[11px] text-purple-600 font-medium mt-0.5">Scope: All Modules</div>
                        )}
                      </td>

                      {/* Company Workspace */}
                      <td className="px-6 py-4">
                        <span className="text-xs text-gray-700 font-medium flex items-center gap-1.5">
                          <Building2 size={13} className="text-gray-400" />
                          {e.company_name || (companies.find(c => c.id === e.company_id)?.name || 'Default Workspace')}
                        </span>
                      </td>

                      {/* Status */}
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 text-xs font-semibold rounded-full ${
                          e.status === 'Active' 
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                            : e.status === 'Pending_Approval'
                            ? 'bg-amber-50 text-amber-700 border border-amber-200 animate-pulse'
                            : 'bg-gray-100 text-gray-600 border border-gray-200'
                        }`}>
                          {e.status}
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {/* Quick Approve button for Pending users */}
                          {e.status === 'Pending_Approval' && (
                            <button
                              onClick={() => handleStatusToggle(e)}
                              className="px-2.5 py-1 text-xs font-bold bg-emerald-600 text-white rounded-md hover:bg-emerald-700 transition shadow-xs flex items-center gap-1"
                              title="Approve & Activate Account"
                            >
                              <UserCheck size={13} /> Approve
                            </button>
                          )}

                          {/* Activate/Deactivate Toggle */}
                          {e.status === 'Active' ? (
                            <button
                              onClick={() => handleStatusToggle(e)}
                              className="p-1.5 text-gray-400 hover:text-amber-600 hover:bg-amber-50 rounded transition"
                              title="Deactivate Account"
                            >
                              <UserX size={16} />
                            </button>
                          ) : e.status === 'Inactive' ? (
                            <button
                              onClick={() => handleStatusToggle(e)}
                              className="p-1.5 text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 rounded transition"
                              title="Activate Account"
                            >
                              <UserCheck size={16} />
                            </button>
                          ) : null}

                          {/* Reset Password Button */}
                          <button
                            onClick={() => {
                              setActiveEmployee(e);
                              setFormError('');
                              setResetFormData({ password: '', confirm_password: '' });
                              setShowResetModal(true);
                            }}
                            className="p-1.5 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded transition"
                            title="Reset User Password"
                          >
                            <KeyRound size={16} />
                          </button>

                          {/* View Details Button */}
                          <button
                            onClick={() => {
                              setActiveEmployee(e);
                              setShowViewModal(true);
                            }}
                            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition"
                            title="View Account Details"
                          >
                            <Eye size={16} />
                          </button>

                          {/* Edit Button */}
                          <button
                            onClick={() => {
                              setEditingId(e.id);
                              setFormError('');
                              setFormData({
                                name: e.name,
                                email: e.email,
                                phone: e.phone || '',
                                department: e.department || '',
                                designation: e.designation || '',
                                password: '',
                                confirm_password: '',
                                role_id: e.role_id || '',
                                company_id: e.company_id || '',
                                status: e.status
                              });
                              setShowModal(true);
                            }}
                            className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded transition"
                            title="Edit User"
                          >
                            <Edit size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* MODAL 1: Create System Administrator Modal */}
      {showAdminModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden border border-gray-100 animate-in fade-in zoom-in-95 duration-150">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-700 to-indigo-700 p-6 text-white">
              <span className="text-xs uppercase font-bold tracking-wider text-purple-200 bg-white/10 px-2.5 py-1 rounded-full flex items-center gap-1.5 w-fit">
                <Shield size={12} /> System Administrator Setup
              </span>
              <h2 className="text-xl font-bold mt-2">Create New System Administrator</h2>
              <p className="text-xs text-purple-100 mt-1">
                Grants full system administrative access to all CRM360 modules with Data Scope: All.
              </p>
            </div>

            {/* Error Banner */}
            {formError && (
              <div className="p-4 bg-red-50 border-b border-red-200 text-red-700 text-xs flex items-center gap-2">
                <AlertTriangle size={16} className="shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleCreateAdmin} className="p-6 space-y-4 text-sm">
              <div>
                <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Full Name *</label>
                <input
                  required
                  type="text"
                  placeholder="e.g. Alexander Vance"
                  value={adminFormData.name}
                  onChange={(e) => setAdminFormData({ ...adminFormData, name: e.target.value })}
                  className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Work Email Address *</label>
                <input
                  required
                  type="email"
                  placeholder="e.g. admin.vance@crm360.com"
                  value={adminFormData.email}
                  onChange={(e) => setAdminFormData({ ...adminFormData, email: e.target.value })}
                  className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Password *</label>
                  <input
                    required
                    type="password"
                    placeholder="Min 8 characters"
                    value={adminFormData.password}
                    onChange={(e) => setAdminFormData({ ...adminFormData, password: e.target.value })}
                    className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Confirm Password *</label>
                  <input
                    required
                    type="password"
                    placeholder="Re-enter password"
                    value={adminFormData.confirm_password}
                    onChange={(e) => setAdminFormData({ ...adminFormData, confirm_password: e.target.value })}
                    className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Company Workspace</label>
                <select
                  value={adminFormData.company_id}
                  onChange={(e) => setAdminFormData({ ...adminFormData, company_id: e.target.value })}
                  className="w-full p-2.5 border border-gray-300 rounded-lg outline-none bg-white"
                >
                  {companies.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              {/* Locked Admin Role & Scope Badge */}
              <div className="p-3 bg-purple-50 border border-purple-100 rounded-xl space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-purple-900 flex items-center gap-1.5">
                    <ShieldCheck size={14} className="text-purple-700" /> Role: System Administrator
                  </span>
                  <span className="text-[11px] font-bold text-purple-700 bg-purple-200/60 px-2 py-0.5 rounded">
                    Data Scope: All
                  </span>
                </div>
                <p className="text-[11px] text-purple-700">
                  Account is granted Active status with 105 permissions across all CRM modules.
                </p>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setShowAdminModal(false)}
                  className="px-4 py-2.5 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-bold shadow-md transition disabled:opacity-50"
                >
                  {actionLoading ? 'Creating Administrator...' : 'Create Administrator'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Add / Edit Standard User Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden border border-gray-100">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">{editingId ? 'Edit Account' : 'Add New User'}</h2>
              <p className="text-xs text-gray-500 mt-1">Configure user identity, assigned role, workspace, and account status.</p>
            </div>

            {formError && (
              <div className="p-4 bg-red-50 border-b border-red-200 text-red-700 text-xs flex items-center gap-2">
                <AlertTriangle size={16} className="shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleStandardSubmit} className="p-6 space-y-4 text-sm max-h-[75vh] overflow-y-auto">
              <div>
                <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Full Name *</label>
                <input
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Work Email Address *</label>
                <input
                  required
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              {!editingId && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Password *</label>
                    <input
                      required
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Confirm Password *</label>
                    <input
                      required
                      type="password"
                      value={formData.confirm_password}
                      onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                      className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Role</label>
                  <select
                    value={formData.role_id}
                    onChange={(e) => setFormData({ ...formData, role_id: e.target.value })}
                    className="w-full p-2.5 border border-gray-300 rounded-lg outline-none bg-white"
                  >
                    <option value="">No Role Assigned</option>
                    {roles.map(r => (
                      <option key={r.id} value={r.id}>{r.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Company Workspace</label>
                  <select
                    value={formData.company_id}
                    onChange={(e) => setFormData({ ...formData, company_id: e.target.value })}
                    className="w-full p-2.5 border border-gray-300 rounded-lg outline-none bg-white"
                  >
                    <option value="">No Company</option>
                    {companies.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Account Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full p-2.5 border border-gray-300 rounded-lg outline-none bg-white"
                  >
                    <option value="Active">Active</option>
                    <option value="Pending_Approval">Pending Approval</option>
                    <option value="Inactive">Inactive</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Phone</label>
                  <input
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="+1 (555) 000-0000"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg shadow-sm disabled:opacity-50"
                >
                  {actionLoading ? 'Saving...' : 'Save User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: Reset Password Modal */}
      {showResetModal && activeEmployee && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl p-6 space-y-4">
            <div className="flex items-center gap-2 text-purple-700 font-bold text-lg">
              <KeyRound size={22} />
              <h3>Reset User Password</h3>
            </div>
            <p className="text-xs text-gray-500">
              Reset credentials for <span className="font-semibold text-gray-800">{activeEmployee.name}</span> ({activeEmployee.email}).
            </p>

            {formError && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg flex items-center gap-2">
                <AlertTriangle size={15} className="shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleResetPassword} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-bold uppercase text-gray-700 mb-1">New Password *</label>
                <input
                  required
                  type="password"
                  placeholder="Min 8 characters, letters & digits"
                  value={resetFormData.password}
                  onChange={(e) => setResetFormData({ ...resetFormData, password: e.target.value })}
                  className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-gray-700 mb-1">Confirm New Password *</label>
                <input
                  required
                  type="password"
                  placeholder="Re-enter new password"
                  value={resetFormData.confirm_password}
                  onChange={(e) => setResetFormData({ ...resetFormData, confirm_password: e.target.value })}
                  className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setShowResetModal(false)}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-5 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-semibold shadow-xs disabled:opacity-50"
                >
                  {actionLoading ? 'Updating...' : 'Update Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 4: View User Details Modal */}
      {showViewModal && activeEmployee && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden border border-gray-100">
            <div className="bg-slate-900 p-6 text-white flex items-center justify-between">
              <div>
                <span className="text-xs uppercase font-bold tracking-wider text-slate-400">Account Details</span>
                <h3 className="text-xl font-bold mt-1">{activeEmployee.name}</h3>
                <p className="text-xs text-slate-300">{activeEmployee.email}</p>
              </div>
              <div className="p-3 bg-white/10 rounded-xl">
                <ShieldCheck size={26} />
              </div>
            </div>

            <div className="p-6 space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500 font-medium">Assigned Role</p>
                  <p className="text-sm font-bold text-gray-900 mt-0.5">{activeEmployee.role_name || 'No Role Assigned'}</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500 font-medium">Account Status</p>
                  <span className={`inline-block mt-0.5 px-2 py-0.5 text-xs font-semibold rounded-full ${
                    activeEmployee.status === 'Active' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                  }`}>
                    {activeEmployee.status}
                  </span>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500 font-medium">Company Workspace</p>
                  <p className="text-sm font-bold text-gray-900 mt-0.5">
                    {activeEmployee.company_name || 'Standard Workspace'}
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500 font-medium">Phone</p>
                  <p className="text-sm font-bold text-gray-900 mt-0.5">{activeEmployee.phone || 'N/A'}</p>
                </div>
              </div>

              <div className="p-3 bg-blue-50 border border-blue-100 rounded-lg text-xs text-blue-900">
                <span className="font-bold">Security Scope:</span> {
                  activeEmployee.role_name === 'System Administrator' 
                    ? 'All Modules & All Scopes (Global System Administrator)' 
                    : 'Governed dynamically by assigned role permissions.'
                }
              </div>

              <div className="flex justify-end pt-3 border-t border-gray-100">
                <button
                  onClick={() => setShowViewModal(false)}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
