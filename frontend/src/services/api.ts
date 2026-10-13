import axios from 'axios';

const API_BASE_URL = '/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT access token to requests automatically
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('scs_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Intercept 401 response and handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    // Don't attempt token refresh if the 401 came from auth endpoints (login or refresh itself)
    const isAuthRequest = originalRequest?.url?.includes('/auth/login') || originalRequest?.url?.includes('/auth/refresh');

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthRequest) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('scs_refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const newAccessToken = res.data.access_token;
          localStorage.setItem('scs_token', newAccessToken);
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return api(originalRequest);
        } catch (refreshErr) {
          localStorage.removeItem('scs_token');
          localStorage.removeItem('scs_refresh_token');
          localStorage.removeItem('scs_user');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);
