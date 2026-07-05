import apiClient from './api';

export async function fetchComplaints(params?: { page?: number; page_size?: number; status?: string; consumer_id?: string }) {
  const { data } = await apiClient.get('/complaints', { params });
  return data;
}

export async function createComplaint(payload: { consumer_id: string; subject: string; description: string; auth_id?: string; channel?: string }) {
  const { data } = await apiClient.post('/complaints', payload);
  return data;
}

export async function resolveComplaint(complaintId: string, payload: { resolution: string }) {
  const { data } = await apiClient.post(`/complaints/${complaintId}/resolve`, payload);
  return data;
}
