import { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, Users, UserSquare2, Briefcase, Building2, MapPin, LogOut, Menu, X } from 'lucide-react';

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navs = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Leads', path: '/leads', icon: Users },
    { name: 'Opportunities', path: '/opportunities', icon: Briefcase },
    { name: 'Customers', path: '/customers', icon: Building2 },
    { name: 'Contacts', path: '/contacts', icon: Users },
    { name: 'Tasks & Meetings', path: '/engagements', icon: MapPin },
    { name: 'Geo-Tracking', path: '/tracking', icon: MapPin },
    { name: 'Reports', path: '/reports', icon: LayoutDashboard },
  ];

  if (user?.role_id === 1) { 
     navs.push({ name: 'Employees', path: '/employees', icon: UserSquare2 });
     navs.push({ name: 'Companies', path: '/companies', icon: Building2 });
     navs.push({ name: 'Roles', path: '/roles', icon: Users });
  }

  return (
    <div className="flex h-screen bg-gray-100 font-sans text-gray-900 overflow-hidden">
      {/* Mobile header */}
      <div className="md:hidden absolute top-0 left-0 w-full h-16 bg-slate-900 text-white flex items-center justify-between px-4 z-20 shadow-md">
        <div className="text-xl font-bold tracking-wider">CRM360</div>
        <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="p-2 text-gray-300 hover:text-white">
          {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Overlay */}
      {isMobileMenuOpen && (
        <div className="md:hidden fixed inset-0 bg-black/50 z-20" onClick={() => setIsMobileMenuOpen(false)}></div>
      )}

      {/* Sidebar */}
      <aside className={`fixed md:relative top-0 left-0 h-full w-64 bg-slate-900 text-white flex flex-col shadow-xl z-30 transition-transform duration-300 ease-in-out ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}>
        <div className="p-5 text-2xl font-bold border-b border-slate-800 tracking-wider hidden md:block">CRM360</div>
        <div className="p-5 border-b border-slate-800 flex items-center justify-between md:hidden">
          <span className="text-xl font-bold tracking-wider">Menu</span>
          <button onClick={() => setIsMobileMenuOpen(false)} className="text-gray-400 hover:text-white"><X size={20}/></button>
        </div>
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {navs.map((n) => {
            const active = location.pathname === n.path || (n.path !== '/' && location.pathname.startsWith(n.path));
            return (
              <Link 
                key={n.path} 
                to={n.path} 
                onClick={() => setIsMobileMenuOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${active ? 'bg-blue-600 text-white shadow-md' : 'text-slate-300 hover:bg-slate-800 hover:text-white'}`}
              >
                <n.icon size={20} />
                <span className="font-medium">{n.name}</span>
              </Link>
            )
          })}
        </nav>
        <div className="p-4 border-t border-slate-800 bg-slate-950">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center font-bold text-lg shadow-inner flex-shrink-0">
              {user?.name?.charAt(0) || 'U'}
            </div>
            <div className="flex-1 overflow-hidden">
              <div className="text-sm font-semibold truncate">{user?.name}</div>
              <div className="text-xs text-slate-400 truncate">{user?.email}</div>
            </div>
          </div>
          <button onClick={logout} className="flex items-center justify-center gap-2 text-slate-300 hover:text-white hover:bg-slate-800 w-full px-3 py-2 rounded-md transition-colors">
            <LogOut size={18} /> <span className="font-medium">Logout</span>
          </button>
        </div>
      </aside>
      
      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-gray-50 pt-16 md:pt-0">
        <Outlet />
      </main>
    </div>
  );
}
