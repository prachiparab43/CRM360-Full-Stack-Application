import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import { 
  User, 
  Shield, 
  Building2, 
  Moon, 
  Sun, 
  LogOut, 
  Check, 
  AlertCircle, 
  Lock, 
  Phone, 
  Briefcase, 
  BadgeCheck, 
  Mail,
  Save,
  Laptop
} from 'lucide-react';

export default function Settings() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  // Active tab state
  const [activeTab, setActiveTab] = useState('profile');

  // Profile editing state
  const [employeeData, setEmployeeData] = useState(null);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [phone, setPhone] = useState('');
  const [department, setDepartment] = useState('');
  const [designation, setDesignation] = useState('');
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileSuccess, setProfileSuccess] = useState('');
  const [profileError, setProfileError] = useState('');

  // Password change state (for email/password users)
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [savingPassword, setSavingPassword] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState('');
  const [passwordError, setPasswordError] = useState('');

  // Company details state (RBAC checked)
  const [companyDetails, setCompanyDetails] = useState(null);
  const [loadingCompany, setLoadingCompany] = useState(false);

  // Theme mode state (persisted in localStorage and applied to root html)
  const [themeMode, setThemeMode] = useState(() => {
    return localStorage.getItem('crm360_theme') || 'system';
  });

  // Apply theme mode
  const applyTheme = (mode) => {
    setThemeMode(mode);
    localStorage.setItem('crm360_theme', mode);
    const root = document.documentElement;
    if (mode === 'dark') {
      root.classList.add('dark');
    } else if (mode === 'light') {
      root.classList.remove('dark');
    } else {
      // System mode
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    }
  };

  // Fetch current employee data and company if permitted
  useEffect(() => {
    const fetchProfileAndCompany = async () => {
      if (!user?.id) return;
      try {
        setLoadingProfile(true);
        // Fetch all employees to find current user's full record
        const empRes = await api.get(`/employees/?search=${encodeURIComponent(user.email)}`);
        const currentEmp = empRes.data.find(e => e.id === user.id) || empRes.data[0];
        if (currentEmp) {
          setEmployeeData(currentEmp);
          setPhone(currentEmp.phone || '');
          setDepartment(currentEmp.department || '');
          setDesignation(currentEmp.designation || '');

          // Check if user has permission to view company details
          const canViewCompany = user.permissions?.some(p => 
            p.module === 'Admin' || (p.module === 'Company' && p.action === 'View')
          );

          if (canViewCompany && currentEmp.company_id) {
            setLoadingCompany(true);
            try {
              const compRes = await api.get('/companies/');
              const myComp = compRes.data.find(c => c.id === currentEmp.company_id);
              if (myComp) setCompanyDetails(myComp);
            } catch (cErr) {
              console.error('Company fetch error:', cErr);
            } finally {
              setLoadingCompany(false);
            }
          }
        }
      } catch (err) {
        console.error('Failed to load profile data:', err);
      } finally {
        setLoadingProfile(false);
      }
    };

    fetchProfileAndCompany();
  }, [user]);

  // Handle Profile Save
  const handleSaveProfile = async (e) => {
    e.preventDefault();
    if (!user?.id) return;
    setSavingProfile(true);
    setProfileSuccess('');
    setProfileError('');

    try {
      await api.put(`/employees/${user.id}`, {
        name: employeeData?.name || user.name,
        email: employeeData?.email || user.email,
        phone: phone.trim() || null,
        department: department.trim() || null,
        designation: designation.trim() || null
      });
      setProfileSuccess('Profile updated successfully.');
      setTimeout(() => setProfileSuccess(''), 4000);
    } catch (err) {
      setProfileError(err.response?.data?.detail || 'Failed to update profile. Please try again.');
    } finally {
      setSavingProfile(false);
    }
  };

  // Handle Password Change (using existing PUT /employees/{id} which hashes password)
  const handleSavePassword = async (e) => {
    e.preventDefault();
    if (!user?.id) return;
    setPasswordSuccess('');
    setPasswordError('');

    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError('New password and confirmation do not match.');
      return;
    }

    // Verify current password first by authenticating with /auth/login
    setSavingPassword(true);
    try {
      const verifyData = new FormData();
      verifyData.append('username', user.email);
      verifyData.append('password', currentPassword);
      await api.post('/auth/login', verifyData);
    } catch (err) {
      setSavingPassword(false);
      setPasswordError('Current password is incorrect.');
      return;
    }

    // If verification succeeded, update password via /employees/{id}
    try {
      await api.put(`/employees/${user.id}`, {
        password: newPassword
      });
      setPasswordSuccess('Password changed successfully.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setTimeout(() => setPasswordSuccess(''), 4000);
    } catch (err) {
      setPasswordError(err.response?.data?.detail || 'Failed to update password.');
    } finally {
      setSavingPassword(false);
    }
  };

  const isGoogleUser = employeeData?.auth_provider === 'google' || Boolean(employeeData?.google_sub);
  const canViewCompany = user?.permissions?.some(p => 
    p.module === 'Admin' || (p.module === 'Company' && p.action === 'View')
  );

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-8 pb-12 font-sans">
      
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Account Settings</h1>
        <p className="text-gray-500 mt-1">Manage your profile, security preferences, and display settings.</p>
      </div>

      {/* Main Grid: Navigation Tabs on Left, Content on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        
        {/* Navigation Tabs Card */}
        <div className="bg-white rounded-xl shadow-xs border border-gray-200/90 overflow-hidden p-2 space-y-1">
          <button
            type="button"
            onClick={() => setActiveTab('profile')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
              activeTab === 'profile' 
                ? 'bg-blue-50 text-blue-700 font-semibold shadow-2xs' 
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
            }`}
          >
            <User size={18} className={activeTab === 'profile' ? 'text-blue-600' : 'text-gray-400'} />
            <span>My Profile</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('security')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
              activeTab === 'security' 
                ? 'bg-blue-50 text-blue-700 font-semibold shadow-2xs' 
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
            }`}
          >
            <Shield size={18} className={activeTab === 'security' ? 'text-blue-600' : 'text-gray-400'} />
            <span>Account & Security</span>
          </button>

          {canViewCompany && (
            <button
              type="button"
              onClick={() => setActiveTab('company')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                activeTab === 'company' 
                  ? 'bg-blue-50 text-blue-700 font-semibold shadow-2xs' 
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
            >
              <Building2 size={18} className={activeTab === 'company' ? 'text-blue-600' : 'text-gray-400'} />
              <span>Company Information</span>
            </button>
          )}

          <button
            type="button"
            onClick={() => setActiveTab('appearance')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
              activeTab === 'appearance' 
                ? 'bg-blue-50 text-blue-700 font-semibold shadow-2xs' 
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
            }`}
          >
            <Sun size={18} className={activeTab === 'appearance' ? 'text-blue-600' : 'text-gray-400'} />
            <span>Appearance</span>
          </button>

          <div className="pt-2 border-t border-gray-100 mt-2">
            <button
              type="button"
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
            >
              <LogOut size={18} className="text-red-500" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>

        {/* Tab Content Panel */}
        <div className="lg:col-span-3 space-y-6">
          
          {/* ========================================================= */}
          {/* TAB 1: MY PROFILE                                         */}
          {/* ========================================================= */}
          {activeTab === 'profile' && (
            <div className="bg-white rounded-xl shadow-xs border border-gray-200/90 overflow-hidden">
              <div className="p-6 border-b border-gray-100 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-gray-900">Personal Information</h2>
                  <p className="text-xs sm:text-sm text-gray-500 mt-0.5">View and update your personal contact and department details.</p>
                </div>
                <div className="flex items-center gap-2 px-3 py-1 bg-blue-50 text-blue-700 text-xs font-semibold rounded-full border border-blue-100">
                  <BadgeCheck size={14} />
                  <span>{user?.role_name || 'Staff Member'}</span>
                </div>
              </div>

              {profileSuccess && (
                <div className="mx-6 mt-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-2.5 text-sm text-emerald-800">
                  <Check size={18} className="text-emerald-600 flex-shrink-0" />
                  <span>{profileSuccess}</span>
                </div>
              )}

              {profileError && (
                <div className="mx-6 mt-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2.5 text-sm text-red-700">
                  <AlertCircle size={18} className="text-red-500 flex-shrink-0" />
                  <span>{profileError}</span>
                </div>
              )}

              <form onSubmit={handleSaveProfile} className="p-6 space-y-5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  {/* Name (Read-only managed field) */}
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1.5">
                      Full Name
                    </label>
                    <input
                      type="text"
                      disabled
                      value={employeeData?.name || user?.name || ''}
                      className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600 cursor-not-allowed"
                    />
                    <p className="text-[11px] text-gray-400 mt-1">Managed via Organizational Administration.</p>
                  </div>

                  {/* Email (Read-only identity field) */}
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1.5">
                      Email Address
                    </label>
                    <div className="relative">
                      <input
                        type="email"
                        disabled
                        value={employeeData?.email || user?.email || ''}
                        className="w-full pl-9 pr-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600 cursor-not-allowed"
                      />
                      <Mail size={16} className="absolute left-3 top-3 text-gray-400" />
                    </div>
                    <p className="text-[11px] text-gray-400 mt-1">Primary identity credential.</p>
                  </div>

                  {/* Phone (Editable) */}
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
                      Phone Number
                    </label>
                    <div className="relative">
                      <input
                        type="tel"
                        placeholder="e.g. +1 555-0199"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        className="w-full pl-9 pr-3.5 py-2.5 bg-white border border-gray-300 rounded-lg text-sm text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 outline-none transition-all"
                      />
                      <Phone size={16} className="absolute left-3 top-3 text-gray-400" />
                    </div>
                  </div>

                  {/* Department (Editable) */}
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
                      Department
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        placeholder="e.g. Sales, Marketing, Executive"
                        value={department}
                        onChange={(e) => setDepartment(e.target.value)}
                        className="w-full pl-9 pr-3.5 py-2.5 bg-white border border-gray-300 rounded-lg text-sm text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 outline-none transition-all"
                      />
                      <Briefcase size={16} className="absolute left-3 top-3 text-gray-400" />
                    </div>
                  </div>

                  {/* Designation (Editable) */}
                  <div className="sm:col-span-2">
                    <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
                      Designation / Title
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Senior Account Executive"
                      value={designation}
                      onChange={(e) => setDesignation(e.target.value)}
                      className="w-full px-3.5 py-2.5 bg-white border border-gray-300 rounded-lg text-sm text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 outline-none transition-all"
                    />
                  </div>
                </div>

                <div className="pt-4 border-t border-gray-100 flex items-center justify-end gap-3">
                  <button
                    type="submit"
                    disabled={savingProfile || loadingProfile}
                    className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm rounded-lg shadow-2xs flex items-center gap-2 transition-all cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    <Save size={16} />
                    <span>{savingProfile ? 'Saving Changes...' : 'Save Profile'}</span>
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB 2: ACCOUNT & SECURITY                                 */}
          {/* ========================================================= */}
          {activeTab === 'security' && (
            <div className="space-y-6">
              {/* Authentication Provider Card */}
              <div className="bg-white rounded-xl shadow-xs border border-gray-200/90 overflow-hidden p-6">
                <h2 className="text-lg font-bold text-gray-900 mb-1">Sign-In Method</h2>
                <p className="text-sm text-gray-500 mb-5">Current identity authentication provider for your enterprise account.</p>

                {isGoogleUser ? (
                  <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-200/80 flex items-start gap-3.5">
                    <div className="w-9 h-9 bg-white rounded-lg flex items-center justify-center shadow-xs flex-shrink-0 mt-0.5 border border-blue-100">
                      <svg className="w-5 h-5" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
                      </svg>
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900 text-sm">Google Workspace / OpenID Connect</div>
                      <p className="text-xs text-gray-600 mt-0.5">
                        Your account authenticates directly via Google Identity Services. Password management and two-factor authentication are secured by your Google Account security settings.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-start gap-3.5">
                    <div className="w-9 h-9 bg-white rounded-lg flex items-center justify-center shadow-xs flex-shrink-0 mt-0.5 border border-slate-200">
                      <Lock size={18} className="text-slate-700" />
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900 text-sm">Standard Email & Password Authentication</div>
                      <p className="text-xs text-gray-600 mt-0.5">
                        Your account is secured with a CRM360 encrypted password hash. You can update your password below.
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Password Change Card (Only shown for password-based accounts) */}
              {!isGoogleUser && (
                <div className="bg-white rounded-xl shadow-xs border border-gray-200/90 overflow-hidden">
                  <div className="p-6 border-b border-gray-100">
                    <h2 className="text-lg font-bold text-gray-900">Change Password</h2>
                    <p className="text-xs sm:text-sm text-gray-500 mt-0.5">Ensure your account is using a strong, unique password.</p>
                  </div>

                  {passwordSuccess && (
                    <div className="mx-6 mt-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-2.5 text-sm text-emerald-800">
                      <Check size={18} className="text-emerald-600 flex-shrink-0" />
                      <span>{passwordSuccess}</span>
                    </div>
                  )}

                  {passwordError && (
                    <div className="mx-6 mt-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2.5 text-sm text-red-700">
                      <AlertCircle size={18} className="text-red-500 flex-shrink-0" />
                      <span>{passwordError}</span>
                    </div>
                  )}

                  <form onSubmit={handleSavePassword} className="p-6 space-y-4 max-w-md">
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
                        Current Password *
                      </label>
                      <input
                        type="password"
                        required
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        className="w-full px-3.5 py-2.5 bg-white border border-gray-300 rounded-lg text-sm text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 outline-none"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
                        New Password *
                      </label>
                      <input
                        type="password"
                        required
                        placeholder="Minimum 8 characters"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className="w-full px-3.5 py-2.5 bg-white border border-gray-300 rounded-lg text-sm text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 outline-none"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
                        Confirm New Password *
                      </label>
                      <input
                        type="password"
                        required
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        className="w-full px-3.5 py-2.5 bg-white border border-gray-300 rounded-lg text-sm text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 outline-none"
                      />
                    </div>

                    <div className="pt-2">
                      <button
                        type="submit"
                        disabled={savingPassword}
                        className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm rounded-lg shadow-2xs flex items-center gap-2 transition-all cursor-pointer disabled:opacity-60"
                      >
                        <Lock size={16} />
                        <span>{savingPassword ? 'Updating Password...' : 'Update Password'}</span>
                      </button>
                    </div>
                  </form>
                </div>
              )}
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB 3: COMPANY INFORMATION (RBAC PROTECTED)               */}
          {/* ========================================================= */}
          {activeTab === 'company' && canViewCompany && (
            <div className="bg-white rounded-xl shadow-xs border border-gray-200/90 overflow-hidden">
              <div className="p-6 border-b border-gray-100">
                <h2 className="text-lg font-bold text-gray-900">Organization Details</h2>
                <p className="text-xs sm:text-sm text-gray-500 mt-0.5">Your affiliated company information as configured in CRM360.</p>
              </div>

              {loadingCompany ? (
                <div className="p-8 text-center text-gray-400 text-sm">Loading company details...</div>
              ) : companyDetails ? (
                <div className="p-6 grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">Company Name</span>
                    <span className="text-base font-bold text-gray-900 mt-1 block">{companyDetails.name}</span>
                  </div>

                  <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">Status</span>
                    <span className="inline-block mt-1 px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800">
                      {companyDetails.status || 'Active'}
                    </span>
                  </div>

                  <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">Email</span>
                    <span className="text-sm font-medium text-gray-800 mt-1 block">{companyDetails.email || 'N/A'}</span>
                  </div>

                  <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">Phone</span>
                    <span className="text-sm font-medium text-gray-800 mt-1 block">{companyDetails.phone || 'N/A'}</span>
                  </div>

                  <div className="sm:col-span-2 p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">Address</span>
                    <span className="text-sm font-medium text-gray-800 mt-1 block whitespace-pre-line">{companyDetails.address || 'N/A'}</span>
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-gray-500 text-sm">
                  No company assigned yet. Contact your System Administrator to be assigned to an organization.
                </div>
              )}
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB 4: APPEARANCE                                         */}
          {/* ========================================================= */}
          {activeTab === 'appearance' && (
            <div className="bg-white rounded-xl shadow-xs border border-gray-200/90 overflow-hidden p-6 space-y-6">
              <div>
                <h2 className="text-lg font-bold text-gray-900">Interface Theme</h2>
                <p className="text-sm text-gray-500 mt-0.5">Select how CRM360 looks on your device.</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {/* Light Theme Card */}
                <button
                  type="button"
                  onClick={() => applyTheme('light')}
                  className={`p-4 rounded-xl border-2 text-left flex flex-col justify-between h-32 transition-all cursor-pointer ${
                    themeMode === 'light' 
                      ? 'border-blue-600 bg-blue-50/40 shadow-xs' 
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between w-full">
                    <Sun size={24} className={themeMode === 'light' ? 'text-blue-600' : 'text-gray-400'} />
                    {themeMode === 'light' && <div className="w-2.5 h-2.5 rounded-full bg-blue-600" />}
                  </div>
                  <div>
                    <div className="font-semibold text-sm text-gray-900">Light Mode</div>
                    <div className="text-xs text-gray-500 mt-0.5">Classic clean enterprise theme</div>
                  </div>
                </button>

                {/* Dark Theme Card */}
                <button
                  type="button"
                  onClick={() => applyTheme('dark')}
                  className={`p-4 rounded-xl border-2 text-left flex flex-col justify-between h-32 transition-all cursor-pointer ${
                    themeMode === 'dark' 
                      ? 'border-blue-600 bg-blue-50/40 shadow-xs' 
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between w-full">
                    <Moon size={24} className={themeMode === 'dark' ? 'text-blue-600' : 'text-gray-400'} />
                    {themeMode === 'dark' && <div className="w-2.5 h-2.5 rounded-full bg-blue-600" />}
                  </div>
                  <div>
                    <div className="font-semibold text-sm text-gray-900">Dark Mode</div>
                    <div className="text-xs text-gray-500 mt-0.5">High contrast, low glare in dim light</div>
                  </div>
                </button>

                {/* System Theme Card */}
                <button
                  type="button"
                  onClick={() => applyTheme('system')}
                  className={`p-4 rounded-xl border-2 text-left flex flex-col justify-between h-32 transition-all cursor-pointer ${
                    themeMode === 'system' 
                      ? 'border-blue-600 bg-blue-50/40 shadow-xs' 
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between w-full">
                    <Laptop size={24} className={themeMode === 'system' ? 'text-blue-600' : 'text-gray-400'} />
                    {themeMode === 'system' && <div className="w-2.5 h-2.5 rounded-full bg-blue-600" />}
                  </div>
                  <div>
                    <div className="font-semibold text-sm text-gray-900">System Default</div>
                    <div className="text-xs text-gray-500 mt-0.5">Follows OS dark/light preferences</div>
                  </div>
                </button>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
