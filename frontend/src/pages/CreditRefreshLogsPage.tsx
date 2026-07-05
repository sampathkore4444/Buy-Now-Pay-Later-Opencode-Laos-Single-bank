import { Box, Typography, Paper, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, TablePagination } from '@mui/material';
import { Refresh } from '@mui/icons-material';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchCreditRefreshLogs, triggerCreditRefresh } from '../services/creditService';

export default function CreditRefreshLogsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);

  const { data, isLoading } = useQuery({
    queryKey: ['credit-refresh-logs', page, rowsPerPage],
    queryFn: () => fetchCreditRefreshLogs({ page: page + 1, page_size: rowsPerPage }),
  });

  const refreshMutation = useMutation({
    mutationFn: triggerCreditRefresh,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credit-refresh-logs'] });
    },
  });

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>Credit Limit Refresh Logs</Typography>
        <Button variant="contained" startIcon={<Refresh />} onClick={() => refreshMutation.mutate()} disabled={refreshMutation.isPending}>
          Refresh Limits
        </Button>
      </Box>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Batch ID</TableCell>
              <TableCell>Total Consumers</TableCell>
              <TableCell>Limits Updated</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Started At</TableCell>
              <TableCell>Completed At</TableCell>
              <TableCell>Error</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.data?.map((log: any) => (
              <TableRow key={log.batch_id}>
                <TableCell><Typography variant="body2" sx={{ fontFamily: 'monospace' }}>{log.batch_id}</Typography></TableCell>
                <TableCell>{log.total_consumers}</TableCell>
                <TableCell>{log.limits_updated}</TableCell>
                <TableCell>
                  <Chip label={log.status} color={log.status === 'COMPLETED' ? 'success' : log.status === 'FAILED' ? 'error' : 'warning'} size="small" />
                </TableCell>
                <TableCell>{log.started_at ? new Date(log.started_at).toLocaleString() : '—'}</TableCell>
                <TableCell>{log.completed_at ? new Date(log.completed_at).toLocaleString() : '—'}</TableCell>
                <TableCell><Typography variant="body2" color="error">{log.error_message || '—'}</Typography></TableCell>
              </TableRow>
            ))}
            {!data?.data?.length && !isLoading && (
              <TableRow><TableCell colSpan={7} align="center">No refresh logs yet</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={data?.pagination?.total || 0}
          page={page}
          onPageChange={(_, p) => setPage(p)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }}
        />
      </TableContainer>
    </Box>
  );
}
