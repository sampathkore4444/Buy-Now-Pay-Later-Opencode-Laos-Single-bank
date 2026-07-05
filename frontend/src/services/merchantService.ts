import apiClient from './api';
import type { Merchant } from '../types';

export async function fetchMerchants(params?: {
  page?: number;
  page_size?: number;
  status?: string;
}): Promise<{ data: Merchant[]; pagination: any }> {
  const { data } = await apiClient.get('/merchants', { params });
  return data;
}

export async function fetchMerchant(merchantId: string): Promise<Merchant> {
  const { data } = await apiClient.get(`/merchants/${merchantId}`);
  return data;
}

export async function onboardMerchant(payload: any): Promise<any> {
  const { data } = await apiClient.post('/merchants/onboard', payload);
  return data;
}

export async function updateMerchant(merchantId: string, payload: any): Promise<Merchant> {
  const { data } = await apiClient.patch(`/merchants/${merchantId}`, payload);
  return data;
}
