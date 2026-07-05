import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  TablePagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
} from '@mui/material';
import { Add } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchMerchants, onboardMerchant } from '../services/merchantService';
import type { Merchant } from '../types';
import { useSnackbar } from 'notistack';

const statusColors: Record<string, 'success' | 'warning' | 'error' | 'default'> = {
  APPROVED: 'success',
  PENDING_KYC: 'warning',
  SUSPENDED: 'error',
  REJECTED: 'error',
};

const riskColors: Record<string, 'success' | 'warning' | 'error'> = {
  GREEN: 'success',
  YELLOW: 'warning',
  ORANGE: 'warning',
  RED: 'error',
};

export default function MerchantsPage() {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);
  const [onboardOpen, setOnboardOpen] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['merchants', page + 1, rowsPerPage],
    queryFn: () => fetchMerchants({ page: page + 1, page_size: rowsPerPage }),
  });

  const onboardMutation = useMutation({
    mutationFn: onboardMerchant,
    onSuccess: () => {
      enqueueSnackbar('Merchant onboarded successfully', { variant: 'success' });
      setOnboardOpen(false);
      queryClient.invalidateQueries({ queryKey: ['merchants'] });
    },
    onError: (err: any) => {
      enqueueSnackbar(err.response?.data?.detail || 'Failed to onboard merchant', { variant: 'error' });
    },
  });

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>Merchants</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={() => setOnboardOpen(true)}>
          Onboard Merchant
        </Button>
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
              <TableCell>Channels</TableCell>
              <TableCell>Created</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow><TableCell colSpan={7} align="center">Loading...</TableCell></TableRow>
            ) : data?.data?.map((m: Merchant) => (
              <TableRow
                key={m.merchant_id}
                hover
                sx={{ cursor: 'pointer' }}
                onClick={() => navigate(`/merchants/${m.merchant_id}`)}
              >
                <TableCell>{m.merchant_id}</TableCell>
                <TableCell>{m.business_name}</TableCell>
                <TableCell>
                  <Chip label={m.status} color={statusColors[m.status] || 'default'} size="small" />
                </TableCell>
                <TableCell>
                  <Chip label={m.risk_tier} color={riskColors[m.risk_tier] || 'default'} size="small" />
                </TableCell>
                <TableCell>{(m.mdr_rate * 100).toFixed(1)}%</TableCell>
                <TableCell>{m.channels?.join(', ')}</TableCell>
                <TableCell>{new Date(m.created_at).toLocaleDateString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={data?.pagination?.total ?? 0}
          page={page}
          onPageChange={(_, p) => setPage(p)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }}
        />
      </TableContainer>

      <Dialog open={onboardOpen} onClose={() => setOnboardOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Onboard New Merchant</DialogTitle>
        <OnboardForm onSubmit={(data) => onboardMutation.mutate(data)} />
      </Dialog>
    </Box>
  );
}

function OnboardForm({ onSubmit }: { onSubmit: (data: any) => void }) {
  const [form, setForm] = useState({
    application_id: '',
    business_name: '',
    business_type: 'SOLE_PROPRIETORSHIP',
    merchant_category: 'ELECTRONICS',
    owner: { name: '', id_card: '', phone: '', email: '' },
    settlement_account: { bank_code: 'BCEL', account_number: '', account_name: '' },
    business_address: { street: '', district: '', province: 'Vientiane Capital' },
    channels: ['LAOQR'],
    estimated_monthly_volume_lak: 50000000,
    registration_number: '',
    tax_id: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <form onSubmit={handleSubmit}>
      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField label="Application ID" required value={form.application_id} onChange={(e) => setForm({ ...form, application_id: e.target.value })} />
          <TextField label="Business Name" required value={form.business_name} onChange={(e) => setForm({ ...form, business_name: e.target.value })} />
          <TextField label="Registration Number" value={form.registration_number} onChange={(e) => setForm({ ...form, registration_number: e.target.value })} />
          <TextField label="Tax ID" value={form.tax_id} onChange={(e) => setForm({ ...form, tax_id: e.target.value })} />
          <TextField label="Merchant Category" value={form.merchant_category} onChange={(e) => setForm({ ...form, merchant_category: e.target.value })} />
          <TextField label="Owner Name" required value={form.owner.name} onChange={(e) => setForm({ ...form, owner: { ...form.owner, name: e.target.value } })} />
          <TextField label="Owner Phone" required value={form.owner.phone} onChange={(e) => setForm({ ...form, owner: { ...form.owner, phone: e.target.value } })} />
          <TextField label="Owner Email" required type="email" value={form.owner.email} onChange={(e) => setForm({ ...form, owner: { ...form.owner, email: e.target.value } })} />
          <TextField label="Settlement Account No" required value={form.settlement_account.account_number} onChange={(e) => setForm({ ...form, settlement_account: { ...form.settlement_account, account_number: e.target.value } })} />
          <TextField label="Settlement Account Name" required value={form.settlement_account.account_name} onChange={(e) => setForm({ ...form, settlement_account: { ...form.settlement_account, account_name: e.target.value } })} />
          <TextField label="Est. Monthly Volume (LAK)" type="number" value={form.estimated_monthly_volume_lak} onChange={(e) => setForm({ ...form, estimated_monthly_volume_lak: Number(e.target.value) })} />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => onSubmit({} as any)}>Cancel</Button>
        <Button type="submit" variant="contained">Submit</Button>
      </DialogActions>
    </form>
  );
}
