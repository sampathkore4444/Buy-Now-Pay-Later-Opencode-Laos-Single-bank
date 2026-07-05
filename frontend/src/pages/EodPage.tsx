import { useState } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Chip, TablePagination, Button, Grid, Card, CardContent } from '@mui/material';
import { PlayArrow } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchEodBatches, fetchEodStatus, triggerEodRun } from '../services/eodService';
import { useSnackbar } from 'notistack';

const statusColors: Record<string, 'success' | 'warning' | 'error' | 'info' | 'default'> = {
  COMPLETED: 'success',
  READY_FOR_PICKUP: 'info',
  IN_PROGRESS: 'warning',
  PARTIAL: 'warning',
  FAILED: 'error',
};

export default function EodPage() {
  const { enqueueSnackbar } = useSnackbar();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);

  const { data: batches } = useQuery({
    queryKey: ['eod-batches', page + 1],
    queryFn: () => fetchEodBatches({ page: page + 1, page_size: 20 }),
  });

  const { data: status } = useQuery({
    queryKey: ['eod-status'],
    queryFn: fetchEodStatus,
    refetchInterval: 10000,
  });

  const triggerMutation = useMutation({
    mutationFn: triggerEodRun,
    onSuccess: () => {
      enqueueSnackbar('EOD batch triggered', { variant: 'success' });
      queryClient.invalidateQueries({ queryKey: ['eod-batches'] });
      queryClient.invalidateQueries({ queryKey: ['eod-status'] });
    },
    onError: () => enqueueSnackbar('Failed to trigger EOD', { variant: 'error' }),
  });

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>EOD Batch Monitor</Typography>
        <Button variant="contained" startIcon={<PlayArrow />} onClick={() => triggerMutation.mutate()}>
          Trigger EOD Run
        </Button>
      </Box>

      {status && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid size={{ xs: 6, sm: 3 }}><Card><CardContent><Typography variant="overline">In Progress</Typography><Typography variant="h6">{status.in_progress}</Typography></CardContent></Card></Grid>
          <Grid size={{ xs: 6, sm: 3 }}><Card><CardContent><Typography variant="overline">Pending</Typography><Typography variant="h6">{status.pending}</Typography></CardContent></Card></Grid>
          <Grid size={{ xs: 6, sm: 3 }}><Card><CardContent><Typography variant="overline">Completed</Typography><Typography variant="h6">{status.completed}</Typography></CardContent></Card></Grid>
          <Grid size={{ xs: 6, sm: 3 }}><Card><CardContent><Typography variant="overline">Failed</Typography><Typography variant="h6">{status.failed}</Typography></CardContent></Card></Grid>
        </Grid>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Batch ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Expected</TableCell>
              <TableCell>Actual</TableCell>
              <TableCell>Start</TableCell>
              <TableCell>End</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {batches?.data?.map((b: any) => (
              <TableRow key={b.batch_id} hover>
                <TableCell>{b.batch_id}</TableCell>
                <TableCell><Chip label={b.control_status} color={statusColors[b.control_status] || 'default'} size="small" /></TableCell>
                <TableCell>{b.expected_record_count}</TableCell>
                <TableCell>{b.actual_record_count}</TableCell>
                <TableCell>{b.eod_start_timestamp ? new Date(b.eod_start_timestamp).toLocaleString() : '—'}</TableCell>
                <TableCell>{b.eod_end_timestamp ? new Date(b.eod_end_timestamp).toLocaleString() : '—'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <TablePagination component="div" count={batches?.pagination?.total ?? 0} page={page} onPageChange={(_, p) => setPage(p)} rowsPerPage={20} rowsPerPageOptions={[20]} />
      </TableContainer>
    </Box>
  );
}
