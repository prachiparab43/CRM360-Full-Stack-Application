import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Landing from './pages/Landing';
import Login from './pages/Login';
import PendingApproval from './pages/PendingApproval';

// Lazy-loaded protected CRM modules
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Companies = lazy(() => import('./pages/Companies'));
const Employees = lazy(() => import('./pages/Employees'));
const Roles = lazy(() => import('./pages/Roles'));
const Leads = lazy(() => import('./pages/Leads'));
const Opportunities = lazy(() => import('./pages/Opportunities'));
const Customers = lazy(() => import('./pages/Customers'));
const Contacts = lazy(() => import('./pages/Contacts'));
const Engagements = lazy(() => import('./pages/Engagements'));
const Tracking = lazy(() => import('./pages/Tracking'));
const Reports = lazy(() => import('./pages/Reports'));
const Settings = lazy(() => import('./pages/Settings'));

// Accessible Loading Fallback for Lazy-Loaded Routes
function PageLoader() {
  return (
    <div 
      className="flex min-h-[50vh] w-full items-center justify-center p-8"
      role="status"
      aria-live="polite"
      aria-label="Loading page content"
    >
      <div className="flex flex-col items-center gap-3">
        <div className="w-10 h-10 border-3 border-blue-600/20 border-t-blue-600 rounded-full animate-spin" />
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
          Loading workspace...
        </span>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public & Authentication Routes (Loaded instantly) */}
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/pending-approval" element={<PendingApproval />} />

          {/* Protected Application Routes (Lazy-loaded with Suspense) */}
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/dashboard" element={<Suspense fallback={<PageLoader />}><Dashboard /></Suspense>} />
              <Route path="/leads" element={<Suspense fallback={<PageLoader />}><Leads /></Suspense>} />
              <Route path="/opportunities" element={<Suspense fallback={<PageLoader />}><Opportunities /></Suspense>} />
              <Route path="/customers" element={<Suspense fallback={<PageLoader />}><Customers /></Suspense>} />
              <Route path="/contacts" element={<Suspense fallback={<PageLoader />}><Contacts /></Suspense>} />
              <Route path="/engagements" element={<Suspense fallback={<PageLoader />}><Engagements /></Suspense>} />
              <Route path="/tracking" element={<Suspense fallback={<PageLoader />}><Tracking /></Suspense>} />
              <Route path="/reports" element={<Suspense fallback={<PageLoader />}><Reports /></Suspense>} />
              <Route path="/employees" element={<Suspense fallback={<PageLoader />}><Employees /></Suspense>} />
              <Route path="/companies" element={<Suspense fallback={<PageLoader />}><Companies /></Suspense>} />
              <Route path="/roles" element={<Suspense fallback={<PageLoader />}><Roles /></Suspense>} />
              <Route path="/settings" element={<Suspense fallback={<PageLoader />}><Settings /></Suspense>} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
