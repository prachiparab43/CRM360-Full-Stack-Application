import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api'
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  response => {
    // Standardize paginated responses { items: [...], total, skip, limit }
    // Attach pagination metadata directly onto items array so both
    // flat array usage (res.data.map) and paginated usage (res.data.total) work seamlessly
    if (response.data && typeof response.data === 'object' && Array.isArray(response.data.items)) {
      const items = response.data.items;
      items.total = response.data.total;
      items.skip = response.data.skip;
      items.limit = response.data.limit;
      items.items = items;
      response.data = items;
    }
    return response;
  },
  error => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      // Only redirect if we are not already on login
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
