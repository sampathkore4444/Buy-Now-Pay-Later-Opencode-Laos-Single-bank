import apiClient from './api';

export async function fetchEodBatches(params?: { page?: number; page_size?: number }) {
  const { data } = await apiClient.get('/eod/batches', { params });
  return data;
}

export async function fetchEodBatch(batchId: string) {
  const { data } = await apiClient.get(`/eod/batches/${batchId}`);
  return data;
}

export async function triggerEodRun() {
  const { data } = await apiClient.post('/eod/run');
  return data;
}

export async function fetchEodStatus() {
  const { data } = await apiClient.get('/eod/status');
  return data;
}
