import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <div className="w-9 h-9 border-3 border-blue-600/20 border-t-blue-600 rounded-full animate-spin" />
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Loading workspace...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/?auth=signin" replace />;
  }

  if (user.status === 'Pending_Approval' || user.status === 'Pending') {
    return <Navigate to="/pending-approval" replace />;
  }

  if (user.status !== 'Active') {
    return <Navigate to="/?auth=signin" replace />;
  }

  return <Outlet />;
}
