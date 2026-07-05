import apiClient from './api';

export async function triggerCreditRefresh() {
  const { data } = await apiClient.post('/credit/refresh');
  return data;
}

export async function fetchCreditRefreshLogs(params?: { page?: number; page_size?: number }) {
  const { data } = await apiClient.get('/credit/refresh-logs', { params });
  return data;
}
