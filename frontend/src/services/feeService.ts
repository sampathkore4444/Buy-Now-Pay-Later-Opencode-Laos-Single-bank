import apiClient from './api';

export async function fetchOverdueTrackers(params?: { page?: number; page_size?: number; status?: string }) {
  const { data } = await apiClient.get('/fees/overdue', { params });
  return data;
}

export async function fetchConsumerOverdue(consumerId: string) {
  const { data } = await apiClient.get(`/fees/overdue/${consumerId}`);
  return data;
}

export async function assessLateFees() {
  const { data } = await apiClient.post('/fees/assess-late-fees');
  return data;
}

export async function assessInterest() {
  const { data } = await apiClient.post('/fees/assess-interest');
  return data;
}
