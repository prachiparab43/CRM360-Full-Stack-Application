import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const res = await api.get('/auth/me');
          setUser(res.data);
        } catch (err) {
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };
    fetchUser();
  }, []);

  const login = async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    const res = await api.post('/auth/login', formData);
    localStorage.setItem('token', res.data.access_token);
    const userRes = await api.get('/auth/me');
    setUser(userRes.data);
    return res.data;
  };

  const googleAuth = async (idToken) => {
    const res = await api.post('/auth/google', { id_token: idToken });
    if (res.data.status === 'Active' && res.data.access_token) {
      localStorage.setItem('token', res.data.access_token);
      const userRes = await api.get('/auth/me');
      setUser(userRes.data);
    }
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, googleAuth, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
