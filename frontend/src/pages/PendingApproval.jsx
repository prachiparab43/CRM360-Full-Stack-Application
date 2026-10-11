import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Clock, ShieldAlert, LogOut, ArrowLeft, Mail, Building2 } from 'lucide-react';

export default function PendingApproval() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center p-4 sm:p-6 font-sans">
      
      {/* Container Card */}
      <div className="w-full max-w-lg bg-white rounded-3xl shadow-xl border border-slate-200/80 p-8 sm:p-10 relative overflow-hidden animate-fade-up">
        
        {/* Top Accent Gradient */}
        <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-amber-500 via-orange-500 to-amber-400" />

        {/* Icon & Status Pill */}
        <div className="flex flex-col items-center text-center mb-6 pt-2">
          <div className="w-16 h-16 rounded-2xl bg-amber-50 border border-amber-200 text-amber-600 flex items-center justify-center mb-4 shadow-xs">
            <Clock size={32} />
          </div>
          
          <div className="inline-flex items-center gap-1.5 bg-amber-100/80 text-amber-800 text-xs font-semibold px-3 py-1 rounded-full border border-amber-200 mb-3">
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
            Account Pending Approval
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
            Welcome to CRM360
          </h1>
          <p className="text-slate-600 text-sm mt-2 max-w-sm">
            Your identity has been authenticated, but your enterprise workspace is not yet active.
          </p>
        </div>

        {/* User Details & Organization Note */}
        <div className="bg-slate-50 rounded-2xl p-5 border border-slate-200/70 space-y-3 mb-6 text-sm">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <span className="text-slate-500 text-xs font-medium">Account Name</span>
            <span className="text-slate-900 font-semibold">{user?.name || 'New User'}</span>
          </div>
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <span className="text-slate-500 text-xs font-medium flex items-center gap-1.5">
              <Mail size={14} className="text-slate-400" />
              Authenticated Email
            </span>
            <span className="text-slate-900 font-mono text-xs">{user?.email || 'N/A'}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-500 text-xs font-medium flex items-center gap-1.5">
              <Building2 size={14} className="text-slate-400" />
              Assigned Company
            </span>
            <span className="text-amber-700 font-medium text-xs bg-amber-100/70 px-2 py-0.5 rounded">
              Awaiting Assignment
            </span>
          </div>
        </div>

        {/* Security & Access Notice */}
        <div className="p-4 rounded-xl bg-blue-50/70 border border-blue-200/60 mb-8 flex items-start gap-3">
          <ShieldAlert size={20} className="text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-blue-900 leading-relaxed">
            <strong className="font-semibold block mb-0.5">Enterprise Data Isolation Policy</strong>
            To protect customer privacy and prevent cross-company data exposure, an authorized System Administrator must assign your Company and Role before access is granted.
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3">
          <button
            onClick={handleLogout}
            className="w-full h-11 bg-slate-900 hover:bg-slate-800 text-white font-medium rounded-xl text-sm flex items-center justify-center gap-2 transition-colors cursor-pointer"
          >
            <LogOut size={16} />
            <span>Sign Out</span>
          </button>
          
          <Link
            to="/"
            className="w-full h-11 bg-white hover:bg-slate-100 text-slate-700 font-medium rounded-xl border border-slate-200 text-sm flex items-center justify-center gap-2 transition-colors"
          >
            <ArrowLeft size={16} />
            <span>Return to Homepage</span>
          </Link>
        </div>

      </div>

      {/* Footer Branding */}
      <p className="text-xs text-slate-400 mt-6 text-center">
        &copy; 2026 CRM360 &bull; Secure Enterprise Platform
      </p>

    </div>
  );
}
