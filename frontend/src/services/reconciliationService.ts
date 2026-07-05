import apiClient from './api';

export async function reconcileBatch(payload: { batch_id: string; expected_count: number; expected_amount: number }) {
  const { data } = await apiClient.post('/reconciliation/batch', payload);
  return data;
}

export async function fetchDailyReport(reportDate?: string) {
  const { data } = await apiClient.get('/reconciliation/daily-report', { params: { report_date: reportDate } });
  return data;
}
