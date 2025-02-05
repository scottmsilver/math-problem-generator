import axios from 'axios';

const instance = axios.create({
  baseURL: 'http://localhost:8081',  // Remove /api prefix
  withCredentials: true,  // Important for CORS with credentials
});

instance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  console.error('Request interceptor error:', error);
  return Promise.reject(error);
});

instance.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Response error:', error.response || error);
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default instance;
