import apiClient from './api';

export async function fetchSettlements(params?: { merchant_id?: string; page?: number; page_size?: number }) {
  const { data } = await apiClient.get('/settlements', { params });
  return data;
}

export async function fetchSettlement(settlementId: string) {
  const { data } = await apiClient.get(`/settlements/${settlementId}`);
  return data;
}
