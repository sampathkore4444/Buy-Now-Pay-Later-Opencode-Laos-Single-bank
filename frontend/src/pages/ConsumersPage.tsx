import { useState } from 'react';
import { Box, Typography, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Chip, TablePagination, Dialog, DialogTitle, DialogContent, DialogActions, TextField } from '@mui/material';
import { Add } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchConsumers, enrollConsumer } from '../services/consumerService';
import { useSnackbar } from 'notistack';

const riskColors: Record<string, 'success' | 'warning' | 'error'> = { GREEN: 'success', YELLOW: 'warning', ORANGE: 'warning', RED: 'error' };

export default function ConsumersPage() {
  const { enqueueSnackbar } = useSnackbar();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState('');
  const [enrollOpen, setEnrollOpen] = useState(false);

  const { data } = useQuery({
    queryKey: ['consumers', page + 1, search],
    queryFn: () => fetchConsumers({ page: page + 1, page_size: 20, search: search || undefined }),
  });

  const enrollMutation = useMutation({
    mutationFn: enrollConsumer,
    onSuccess: () => {
      enqueueSnackbar('Consumer enrolled', { variant: 'success' });
      setEnrollOpen(false);
      queryClient.invalidateQueries({ queryKey: ['consumers'] });
    },
    onError: (err: any) => enqueueSnackbar(err.response?.data?.detail || 'Enrollment failed', { variant: 'error' }),
  });

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>Consumers</Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField size="small" placeholder="Search consumers..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(0); }} />
          <Button variant="contained" startIcon={<Add />} onClick={() => setEnrollOpen(true)}>Enroll Consumer</Button>
        </Box>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Consumer ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Phone</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>BNPL Limit</TableCell>
              <TableCell>Available</TableCell>
              <TableCell>Risk Tier</TableCell>
              <TableCell>Active</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.data?.map((c: any) => (
              <TableRow key={c.consumer_id} hover>
                <TableCell>{c.consumer_id}</TableCell>
                <TableCell>{c.name}</TableCell>
                <TableCell>{c.phone}</TableCell>
                <TableCell>{c.email || '—'}</TableCell>
                <TableCell>{Number(c.bnpl_limit_lak).toLocaleString()}</TableCell>
                <TableCell>{Number(c.available_limit_lak).toLocaleString()}</TableCell>
                <TableCell><Chip label={c.risk_tier} color={riskColors[c.risk_tier] || 'default'} size="small" /></TableCell>
                <TableCell><Chip label={c.is_active ? 'Yes' : 'No'} color={c.is_active ? 'success' : 'error'} size="small" /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <TablePagination component="div" count={data?.pagination?.total ?? 0} page={page} onPageChange={(_, p) => setPage(p)} rowsPerPage={20} rowsPerPageOptions={[20]} />
      </TableContainer>

      <Dialog open={enrollOpen} onClose={() => setEnrollOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Enroll Consumer</DialogTitle>
        <EnrollForm onSubmit={(payload) => enrollMutation.mutate(payload)} />
      </Dialog>
    </Box>
  );
}

function EnrollForm({ onSubmit }: { onSubmit: (data: any) => void }) {
  const [form, setForm] = useState({ bank_customer_id: '', name: '', phone: '', email: '' });
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(form); }}>
      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField label="Bank Customer ID" required value={form.bank_customer_id} onChange={(e) => setForm({ ...form, bank_customer_id: e.target.value })} />
          <TextField label="Name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <TextField label="Phone" required value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <TextField label="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => onSubmit({} as any)}>Cancel</Button>
        <Button type="submit" variant="contained">Submit</Button>
      </DialogActions>
    </form>
  );
}
