import { useAuth } from '../context/AuthContext';
import Unauthorized from '../pages/Unauthorized';

export default function PermissionGate({ module, action = 'View', alternatePermissions = [], children }) {
  const { user } = useAuth();

  if (!module) return children;

  const userPerms = user?.permissions || [];

  // Check primary permission
  let hasPerm = userPerms.some(
    p => (p.module === module || (module === 'Geo' && p.module === 'GeoTracking')) &&
         (p.action === action || (module === 'Geo' && action === 'View' && p.action.startsWith('Geo.')))
  );

  // Check alternate permissions if provided (e.g. for engagements: Task, Meeting, or Activity)
  if (!hasPerm && alternatePermissions.length > 0) {
    hasPerm = alternatePermissions.some(alt =>
      userPerms.some(p => p.module === alt.module && p.action === (alt.action || 'View'))
    );
  }

  if (!hasPerm) {
    return <Unauthorized />;
  }

  return children;
}
