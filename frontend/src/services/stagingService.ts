import apiClient from './api';

export async function writeStagingTransaction(payload: any) {
  const { data } = await apiClient.post('/staging/transactions', payload);
  return data;
}

export async function fetchStagingStatus(correlationId: string) {
  const { data } = await apiClient.get(`/staging/transactions/${correlationId}`);
  return data;
}
