import apiClient from './api';

export async function fetchWebhookLogs(params?: { merchant_id?: string; page?: number; page_size?: number }) {
  const { data } = await apiClient.get('/webhooks/logs', { params });
  return data;
}
