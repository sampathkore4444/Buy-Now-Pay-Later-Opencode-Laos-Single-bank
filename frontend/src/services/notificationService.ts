import apiClient from './api';

export async function fetchNotifications(params?: { page?: number; page_size?: number; channel?: string; status?: string }) {
  const { data } = await apiClient.get('/notifications', { params });
  return data;
}
