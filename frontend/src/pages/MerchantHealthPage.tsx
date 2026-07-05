import { useState } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Chip, TablePagination } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { fetchMerchants } from '../services/merchantService';

const riskColors: Record<string, 'success' | 'warning' | 'error'> = { GREEN: 'success', YELLOW: 'warning', ORANGE: 'warning', RED: 'error' };
const statusColors: Record<string, 'success' | 'warning' | 'error'> = { APPROVED: 'success', PENDING_KYC: 'warning', SUSPENDED: 'error', REJECTED: 'error' };

export default function MerchantHealthPage() {
  const [page, setPage] = useState(0);

  const { data } = useQuery({
    queryKey: ['merchants', 'health', page + 1],
    queryFn: () => fetchMerchants({ page: page + 1, page_size: 50 }),
  });

  const merchants = data?.data ?? [];

  const total = merchants.length;
  const approved = merchants.filter((m: any) => m.status === 'APPROVED').length;
  const green = merchants.filter((m: any) => m.risk_tier === 'GREEN').length;
  const red = merchants.filter((m: any) => m.risk_tier === 'RED').length;

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Merchant Health</Typography>

      <Box sx={{ display: 'flex', gap: 3, mb: 3 }}>
        <Paper sx={{ p: 2, flex: 1 }}><Typography variant="overline">Total Merchants</Typography><Typography variant="h5">{data?.pagination?.total ?? 0}</Typography></Paper>
        <Paper sx={{ p: 2, flex: 1 }}><Typography variant="overline">Approved</Typography><Typography variant="h5" color="success.main">{approved}</Typography></Paper>
        <Paper sx={{ p: 2, flex: 1 }}><Typography variant="overline">Low Risk (GREEN)</Typography><Typography variant="h5" color="success.main">{green}</Typography></Paper>
        <Paper sx={{ p: 2, flex: 1 }}><Typography variant="overline">High Risk (RED)</Typography><Typography variant="h5" color="error.main">{red}</Typography></Paper>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Merchant ID</TableCell>
              <TableCell>Business Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Risk Tier</TableCell>
              <TableCell>MDR Rate</TableCell>
              <TableCell>Daily Limit</TableCell>
              <TableCell>Monthly Limit</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {merchants.map((m: any) => (
              <TableRow key={m.merchant_id} hover>
                <TableCell>{m.merchant_id}</TableCell>
                <TableCell>{m.business_name}</TableCell>
                <TableCell><Chip label={m.status} color={statusColors[m.status] || 'default'} size="small" /></TableCell>
                <TableCell><Chip label={m.risk_tier} color={riskColors[m.risk_tier] || 'default'} size="small" /></TableCell>
                <TableCell>{(m.mdr_rate * 100).toFixed(1)}%</TableCell>
                <TableCell>{m.daily_limit_lak ? `${(m.daily_limit_lak / 1_000_000).toFixed(1)}M` : 'N/A'}</TableCell>
                <TableCell>{m.monthly_limit_lak ? `${(m.monthly_limit_lak / 1_000_000).toFixed(1)}M` : 'N/A'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <TablePagination component="div" count={data?.pagination?.total ?? 0} page={page} onPageChange={(_, p) => setPage(p)} rowsPerPage={50} rowsPerPageOptions={[50]} />
      </TableContainer>
    </Box>
  );
}
