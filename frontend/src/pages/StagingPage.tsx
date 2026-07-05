import { useState } from 'react';
import { Box, Typography, Button, TextField, Paper, Grid, Card, CardContent } from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import { writeStagingTransaction, fetchStagingStatus } from '../services/stagingService';
import { useSnackbar } from 'notistack';

export default function StagingPage() {
  const { enqueueSnackbar } = useSnackbar();
  const [correlationId, setCorrelationId] = useState('');
  const [statusResult, setStatusResult] = useState<any>(null);

  const [form, setForm] = useState({
    batch_id: '',
    source_ref_no: '',
    source_timestamp: new Date().toISOString().slice(0, 16),
    txn_type: 'BNPL',
    txn_category: 'BNPL_PURCHASE',
    txn_amount: '',
    debit_account_no: '',
    credit_account_no: '',
    narrative: '',
  });

  const writeMutation = useMutation({
    mutationFn: () => writeStagingTransaction({ ...form, txn_amount: Number(form.txn_amount), source_timestamp: new Date(form.source_timestamp).toISOString() }),
    onSuccess: (data) => {
      enqueueSnackbar(`Staged: ${data.correlation_id}`, { variant: 'success' });
      setCorrelationId(data.correlation_id);
    },
    onError: (err: any) => enqueueSnackbar(err.response?.data?.detail || 'Staging failed', { variant: 'error' }),
  });

  const checkStatus = async () => {
    if (!correlationId) return;
    try {
      const result = await fetchStagingStatus(correlationId);
      setStatusResult(result);
    } catch {
      enqueueSnackbar('Failed to fetch status', { variant: 'error' });
    }
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Staging Monitor</Typography>

      <Grid container spacing={3}>
        <Grid xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Write Staging Transaction</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField label="Batch ID" required value={form.batch_id} onChange={(e) => setForm({ ...form, batch_id: e.target.value })} />
              <TextField label="Source Ref No" required value={form.source_ref_no} onChange={(e) => setForm({ ...form, source_ref_no: e.target.value })} />
              <TextField label="Source Timestamp" type="datetime-local" value={form.source_timestamp} onChange={(e) => setForm({ ...form, source_timestamp: e.target.value })} InputLabelProps={{ shrink: true }} />
              <TextField label="Amount (LAK)" type="number" required value={form.txn_amount} onChange={(e) => setForm({ ...form, txn_amount: e.target.value })} />
              <TextField label="Debit Account" value={form.debit_account_no} onChange={(e) => setForm({ ...form, debit_account_no: e.target.value })} />
              <TextField label="Credit Account" value={form.credit_account_no} onChange={(e) => setForm({ ...form, credit_account_no: e.target.value })} />
              <TextField label="Narrative" value={form.narrative} onChange={(e) => setForm({ ...form, narrative: e.target.value })} />
              <Button variant="contained" onClick={() => writeMutation.mutate()} disabled={!form.batch_id || !form.source_ref_no || !form.txn_amount}>
                Write to Staging
              </Button>
            </Box>
          </Paper>
        </Grid>

        <Grid xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Check Status</Typography>
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <TextField fullWidth label="Correlation ID" value={correlationId} onChange={(e) => setCorrelationId(e.target.value)} />
              <Button variant="contained" onClick={checkStatus} disabled={!correlationId}>Check</Button>
            </Box>
            {statusResult && (
              <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
                <Typography>Status: <b>{statusResult.status}</b></Typography>
                <Typography>Retry Count: {statusResult.retry_count}</Typography>
                {statusResult.eod_batch_run_id && <Typography>EOD Batch: {statusResult.eod_batch_run_id}</Typography>}
                {statusResult.eod_posting_timestamp && <Typography>Posted: {new Date(statusResult.eod_posting_timestamp).toLocaleString()}</Typography>}
                {statusResult.eod_failure_reason && <Typography color="error">Error: {statusResult.eod_failure_reason}</Typography>}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
