import { useState } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Chip, TablePagination } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { fetchWebhookLogs } from '../services/webhookService';

const statusColors: Record<string, 'success' | 'warning' | 'error' | 'info'> = {
  RECEIVED: 'info',
  DELIVERED: 'success',
  FAILED: 'error',
  RETRY: 'warning',
};

export default function WebhooksPage() {
  const [page, setPage] = useState(0);
  const [merchantFilter, setMerchantFilter] = useState('');

  const { data } = useQuery({
    queryKey: ['webhook-logs', page + 1, merchantFilter],
    queryFn: () => fetchWebhookLogs({ page: page + 1, page_size: 20, merchant_id: merchantFilter || undefined }),
  });

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Webhook Logs</Typography>

      <Box sx={{ mb: 2 }}>
        <input
          placeholder="Filter by Merchant ID"
          value={merchantFilter}
          onChange={(e) => { setMerchantFilter(e.target.value); setPage(0); }}
          style={{ padding: '8px 12px', border: '1px solid #ccc', borderRadius: 4, width: 300 }}
        />
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Merchant ID</TableCell>
              <TableCell>Event Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Response Code</TableCell>
              <TableCell>Created</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.data?.map((log: any) => (
              <TableRow key={log.id} hover>
                <TableCell>{log.id}</TableCell>
                <TableCell>{log.merchant_id}</TableCell>
                <TableCell><Chip label={log.event_type} size="small" /></TableCell>
                <TableCell><Chip label={log.status} color={statusColors[log.status] || 'default'} size="small" /></TableCell>
                <TableCell>{log.response_code || '—'}</TableCell>
                <TableCell>{log.created_at ? new Date(log.created_at).toLocaleString() : '—'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <TablePagination component="div" count={data?.pagination?.total ?? 0} page={page} onPageChange={(_, p) => setPage(p)} rowsPerPage={20} rowsPerPageOptions={[20]} />
      </TableContainer>
    </Box>
  );
}
