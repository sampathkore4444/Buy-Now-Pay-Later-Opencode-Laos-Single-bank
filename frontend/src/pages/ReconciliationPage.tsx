import { useState } from 'react';
import { Box, Typography, Paper, TextField, Button, Grid, Card, CardContent } from '@mui/material';
import { useQuery, useMutation } from '@tanstack/react-query';
import { reconcileBatch, fetchDailyReport } from '../services/reconciliationService';
import { useSnackbar } from 'notistack';

export default function ReconciliationPage() {
  const { enqueueSnackbar } = useSnackbar();
  const [batchId, setBatchId] = useState('');
  const [expectedCount, setExpectedCount] = useState('');
  const [expectedAmount, setExpectedAmount] = useState('');
  const [reportDate, setReportDate] = useState(new Date().toISOString().split('T')[0]);

  const { data: report, refetch: refetchReport } = useQuery({
    queryKey: ['daily-reconcile', reportDate],
    queryFn: () => fetchDailyReport(reportDate),
    enabled: false,
  });

  const reconcileMutation = useMutation({
    mutationFn: () => reconcileBatch({ batch_id: batchId, expected_count: Number(expectedCount), expected_amount: Number(expectedAmount) }),
    onSuccess: (data) => {
      enqueueSnackbar(`Reconciliation: ${data.status}`, { variant: data.status === 'BALANCED' ? 'success' : 'warning' });
    },
    onError: () => enqueueSnackbar('Reconciliation failed', { variant: 'error' }),
  });

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Reconciliation</Typography>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Batch Reconciliation</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField label="Batch ID" value={batchId} onChange={(e) => setBatchId(e.target.value)} required />
              <TextField label="Expected Count" type="number" value={expectedCount} onChange={(e) => setExpectedCount(e.target.value)} required />
              <TextField label="Expected Amount (LAK)" type="number" value={expectedAmount} onChange={(e) => setExpectedAmount(e.target.value)} required />
              <Button variant="contained" onClick={() => reconcileMutation.mutate()} disabled={!batchId || !expectedCount}>
                Reconcile
              </Button>
            </Box>
            {reconcileMutation.data && (
              <Box sx={{ mt: 2, p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
                <Typography>Status: <b>{reconcileMutation.data.status}</b></Typography>
                <Typography>Expected: {reconcileMutation.data.expected_count} / Actual: {reconcileMutation.data.actual_count}</Typography>
                <Typography>Difference: {reconcileMutation.data.count_difference} txns, {Number(reconcileMutation.data.amount_difference).toLocaleString()} LAK</Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Daily Report</Typography>
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <TextField label="Date" type="date" value={reportDate} onChange={(e) => setReportDate(e.target.value)} InputLabelProps={{ shrink: true }} />
              <Button variant="contained" onClick={() => refetchReport()}>Load</Button>
            </Box>
            {report && (
              <Box>
                <Grid container spacing={1}>
                  <Grid size={{ xs: 6 }}><Card><CardContent><Typography variant="overline">Staged</Typography><Typography variant="h6">{report.staged_count}</Typography></CardContent></Card></Grid>
                  <Grid size={{ xs: 6 }}><Card><CardContent><Typography variant="overline">Posted</Typography><Typography variant="h6">{report.posted_count}</Typography></CardContent></Card></Grid>
                  <Grid size={{ xs: 6 }}><Card><CardContent><Typography variant="overline">Failed</Typography><Typography variant="h6">{report.failed_count}</Typography></CardContent></Card></Grid>
                  <Grid size={{ xs: 6 }}><Card><CardContent><Typography variant="overline">Pending</Typography><Typography variant="h6">{report.pending_count}</Typography></CardContent></Card></Grid>
                </Grid>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
