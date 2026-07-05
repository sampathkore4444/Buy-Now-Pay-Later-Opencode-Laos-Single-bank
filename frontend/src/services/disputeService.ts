import apiClient from './api';

export async function initiateDispute(payload: { consumer_id: string; auth_id: string; reason: string; description?: string }) {
  const { data } = await apiClient.post('/disputes/initiate', payload);
  return data;
}

export async function checkCoolingOff(consumerId: string, authId: string) {
  const { data } = await apiClient.get(`/disputes/cooling-off/${consumerId}/${authId}`);
  return data;
}

export async function cancelCoolingOff(consumerId: string, authId: string) {
  const { data } = await apiClient.post('/disputes/cooling-off/cancel', null, { params: { consumer_id: consumerId, auth_id: authId } });
  return data;
}

export async function resolveDispute(disputeId: string, payload: { resolution: string; notes?: string }) {
  const { data } = await apiClient.post(`/disputes/${disputeId}/resolve`, payload);
  return data;
}

export async function fetchConsumerDisputes(consumerId: string) {
  const { data } = await apiClient.get(`/disputes/consumer/${consumerId}`);
  return data;
}
