import { Navigate } from 'react-router-dom';

/**
 * Legacy standalone login page removed per requirement.
 * All authentication is centralized on the homepage modal.
 */
export default function Login() {
  return <Navigate to="/?auth=signin" replace />;
}
