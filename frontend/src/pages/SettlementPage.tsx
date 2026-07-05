import { useState } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Chip, TablePagination } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { fetchSettlements } from '../services/settlementService';
import type { Settlement } from '../types';

const statusColors: Record<string, 'success' | 'warning' | 'error' | 'info'> = {
  PENDING: 'warning',
  PROCESSING: 'info',
  STAGED: 'info',
  COMPLETED: 'success',
  FAILED: 'error',
};

export default function SettlementPage() {
  const [page, setPage] = useState(0);

  const { data, isLoading } = useQuery({
    queryKey: ['settlements', page + 1],
    queryFn: () => fetchSettlements({ page: page + 1, page_size: 20 }),
  });

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Settlements</Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Settlement ID</TableCell>
              <TableCell>Merchant ID</TableCell>
              <TableCell>Date</TableCell>
              <TableCell>Transactions</TableCell>
              <TableCell>Gross Amount</TableCell>
              <TableCell>MDR</TableCell>
              <TableCell>Net Amount</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow><TableCell colSpan={8} align="center">Loading...</TableCell></TableRow>
            ) : data?.data?.length ? (
              data.data.map((s: Settlement) => (
                <TableRow key={s.settlement_id} hover>
                  <TableCell>{s.settlement_id}</TableCell>
                  <TableCell>{s.merchant_id}</TableCell>
                  <TableCell>{new Date(s.settlement_date).toLocaleDateString()}</TableCell>
                  <TableCell>{s.total_txn_count}</TableCell>
                  <TableCell>{Number(s.total_gross_amount).toLocaleString()}</TableCell>
                  <TableCell>{Number(s.total_mdr_amount).toLocaleString()}</TableCell>
                  <TableCell>{Number(s.total_net_amount).toLocaleString()}</TableCell>
                  <TableCell><Chip label={s.status} color={statusColors[s.status] || 'default'} size="small" /></TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow><TableCell colSpan={8} align="center">No settlement data yet</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={data?.pagination?.total ?? 0}
          page={page}
          onPageChange={(_, p) => setPage(p)}
          rowsPerPage={20}
          rowsPerPageOptions={[20]}
        />
      </TableContainer>
    </Box>
  );
}
