import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const getMetrics = (params) => api.get('/metrics', { params });
export const getForecasts = (params) => api.get('/forecasts', { params });
export const getProductForecast = (productId, params) => api.get(`/forecasts/${productId}`, { params });

export default api;