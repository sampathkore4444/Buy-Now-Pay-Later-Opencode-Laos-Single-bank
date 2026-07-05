import { Box, Typography, Paper, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, TablePagination } from '@mui/material';
import { Warning } from '@mui/icons-material';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchOverdueTrackers, assessLateFees, assessInterest } from '../services/feeService';

export default function OverdueTrackerPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);

  const { data, isLoading } = useQuery({
    queryKey: ['overdue', page, rowsPerPage],
    queryFn: () => fetchOverdueTrackers({ page: page + 1, page_size: rowsPerPage }),
  });

  const lateFeeMutation = useMutation({
    mutationFn: assessLateFees,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['overdue'] }),
  });

  const interestMutation = useMutation({
    mutationFn: assessInterest,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['overdue'] }),
  });

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>Overdue Tracker</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" color="warning" startIcon={<Warning />} onClick={() => lateFeeMutation.mutate()} disabled={lateFeeMutation.isPending}>
            Assess Late Fees
          </Button>
          <Button variant="outlined" color="info" onClick={() => interestMutation.mutate()} disabled={interestMutation.isPending}>
            Assess Interest
          </Button>
        </Box>
      </Box>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Consumer</TableCell>
              <TableCell>Overdue Date</TableCell>
              <TableCell>Days Overdue</TableCell>
              <TableCell>Overdue Amount (LAK)</TableCell>
              <TableCell>Late Fee Charged</TableCell>
              <TableCell>Interest Charged</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Last Fee</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.data?.map((t: any) => (
              <TableRow key={t.consumer_id}>
                <TableCell><Typography fontWeight={500}>{t.consumer_id}</Typography></TableCell>
                <TableCell>{t.overdue_date}</TableCell>
                <TableCell><Chip label={t.days_overdue} color={t.days_overdue > 60 ? 'error' : t.days_overdue > 30 ? 'warning' : 'default'} size="small" /></TableCell>
                <TableCell>{Number(t.overdue_amount_lak).toLocaleString()}</TableCell>
                <TableCell>{Number(t.late_fee_charged).toLocaleString()}</TableCell>
                <TableCell>{Number(t.interest_charged).toLocaleString()}</TableCell>
                <TableCell><Chip label={t.status} color={t.status === 'ACTIVE' ? 'error' : 'success'} size="small" /></TableCell>
                <TableCell>{t.last_fee_assessment || '—'}</TableCell>
              </TableRow>
            ))}
            {!data?.data?.length && !isLoading && (
              <TableRow><TableCell colSpan={8} align="center">No overdue records</TableCell></TableRow>
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
