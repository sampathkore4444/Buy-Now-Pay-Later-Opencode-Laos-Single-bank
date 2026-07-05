import { useState } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  TablePagination,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../services/api';
import type { Transaction } from '../types';

export default function TransactionsPage() {
  const [page, setPage] = useState(0);

  const { data, isLoading } = useQuery({
    queryKey: ['transactions', page + 1],
    queryFn: () => apiClient.get('/transactions', { params: { page: page + 1, page_size: 20 } }).then(r => r.data),
  });

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Transactions</Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>TXN ID</TableCell>
              <TableCell>Auth ID</TableCell>
              <TableCell>Merchant ID</TableCell>
              <TableCell>Consumer ID</TableCell>
              <TableCell>Amount (LAK)</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Date</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow><TableCell colSpan={8} align="center">Loading...</TableCell></TableRow>
            ) : data?.data?.map((t: Transaction) => (
              <TableRow key={t.txn_id} hover>
                <TableCell>{t.txn_id}</TableCell>
                <TableCell>{t.auth_id || '—'}</TableCell>
                <TableCell>{t.merchant_id}</TableCell>
                <TableCell>{t.consumer_id}</TableCell>
                <TableCell>{Number(t.amount_lak).toLocaleString()}</TableCell>
                <TableCell>{t.txn_category}</TableCell>
                <TableCell>
                  <Chip label={t.status} size="small" color={t.status === 'CONFIRMED' ? 'success' : 'default'} />
                </TableCell>
                <TableCell>{new Date(t.created_at).toLocaleDateString()}</TableCell>
              </TableRow>
            ))}
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
