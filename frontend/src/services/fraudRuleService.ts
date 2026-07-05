import apiClient from './api';

export async function fetchFraudRules() {
  const { data } = await apiClient.get('/fraud-rules');
  return data;
}

export async function createFraudRule(payload: {
  rule_name: string; rule_type: string; parameter: string; threshold: string; action: string; enabled?: boolean;
}) {
  const { data } = await apiClient.post('/fraud-rules', payload);
  return data;
}

export async function updateFraudRule(ruleId: number, payload: Record<string, any>) {
  const { data } = await apiClient.put(`/fraud-rules/${ruleId}`, payload);
  return data;
}

export async function deleteFraudRule(ruleId: number) {
  const { data } = await apiClient.delete(`/fraud-rules/${ruleId}`);
  return data;
}
