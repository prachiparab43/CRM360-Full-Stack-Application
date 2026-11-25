import { Link } from 'react-router-dom';
import { ShieldX, LayoutDashboard, ArrowLeft } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Unauthorized() {
  const { user } = useAuth();

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center p-6 text-center font-sans">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-slate-200 p-8 animate-fade-up">
        
        <div className="w-16 h-16 rounded-2xl bg-red-50 border border-red-200 text-red-600 flex items-center justify-center mx-auto mb-4 shadow-2xs">
          <ShieldX size={32} />
        </div>

        <span className="inline-flex items-center gap-1.5 bg-red-100 text-red-800 text-xs font-semibold px-3 py-1 rounded-full mb-3">
          HTTP 403 &bull; Access Denied
        </span>

        <h1 className="text-2xl font-bold tracking-tight text-slate-900 mb-2">
          Unauthorized Access
        </h1>

        <p className="text-slate-600 text-sm leading-relaxed mb-6">
          Your current role (<strong className="text-slate-900">{user?.role_name || 'Assigned Role'}</strong>) does not have sufficient permission to view or manage this CRM module.
        </p>

        <div className="space-y-3">
          <Link
            to="/dashboard"
            className="w-full h-11 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl text-sm flex items-center justify-center gap-2 transition-colors shadow-2xs"
          >
            <LayoutDashboard size={16} />
            <span>Return to Dashboard</span>
          </Link>
          
          <button
            type="button"
            onClick={() => window.history.back()}
            className="w-full h-11 bg-white hover:bg-slate-100 text-slate-700 font-medium rounded-xl border border-slate-200 text-sm flex items-center justify-center gap-2 transition-colors cursor-pointer"
          >
            <ArrowLeft size={16} />
            <span>Go Back</span>
          </button>
        </div>

      </div>
    </div>
  );
}
