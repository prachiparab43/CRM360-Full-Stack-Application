import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [pendingUser, setPendingUser] = useState(() => {
    try {
      const saved = sessionStorage.getItem('crm360_pending_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const res = await api.get('/auth/me');
          setUser(res.data);
          if (res.data?.status === 'Pending_Approval' || res.data?.status === 'Pending') {
            setPending(res.data);
          }
        } catch (err) {
          localStorage.removeItem('token');
          setUser(null);
        }
      }
      setLoading(false);
    };
    fetchUser();
  }, []);

  const setPending = (userData) => {
    setPendingUser(userData);
    if (userData) {
      sessionStorage.setItem('crm360_pending_user', JSON.stringify(userData));
    } else {
      sessionStorage.removeItem('crm360_pending_user');
    }
  };

  const login = async (username, password) => {
    const formData = new FormData();
    formData.append('username', username.trim());
    formData.append('password', password);
    const res = await api.post('/auth/login', formData);
    localStorage.setItem('token', res.data.access_token);
    sessionStorage.removeItem('crm360_pending_user');
    const userRes = await api.get('/auth/me');
    const userData = {
      ...userRes.data,
      status: userRes.data?.status || res.data?.status || 'Active'
    };
    setUser(userData);
    return userData;
  };

  const register = async ({ name, email, password, confirm_password, phone }) => {
    const res = await api.post('/auth/register', {
      name: name.trim(),
      email: email.trim(),
      password,
      confirm_password,
      phone: phone ? phone.trim() : null
    });
    if (res.data?.user) {
      setPending(res.data.user);
    }
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('token');
    sessionStorage.removeItem('crm360_pending_user');
    setUser(null);
    setPendingUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, pendingUser, setPending, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

