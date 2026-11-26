import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token_atividros');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const urlRequisicao = error.config?.url || '';
    const ehRotaLogin = urlRequisicao.includes('/autenticacao/entrar');

    if (error.response && error.response.status === 401 && !ehRotaLogin) {
      localStorage.removeItem('token_atividros');
      window.dispatchEvent(new CustomEvent('atividros:sessao-expirada'));

      if (window.location.pathname !== '/login') {
        window.location.assign('/login?sessao=expirada');
      }
    }
    return Promise.reject(error);
  }
);

export default api;
