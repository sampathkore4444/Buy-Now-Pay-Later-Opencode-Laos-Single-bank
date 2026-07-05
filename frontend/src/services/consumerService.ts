import apiClient from './api';

export async function fetchConsumers(params?: { page?: number; page_size?: number; search?: string }) {
  const { data } = await apiClient.get('/consumers', { params });
  return data;
}

export async function enrollConsumer(payload: { bank_customer_id: string; name: string; phone: string; email?: string }) {
  const { data } = await apiClient.post('/consumers/enroll', payload);
  return data;
}

export async function fetchConsumerLimit(consumerId: string) {
  const { data } = await apiClient.get(`/consumers/${consumerId}/limit`);
  return data;
}
