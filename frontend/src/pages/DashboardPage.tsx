import { Box, Grid, Paper, Typography, Card, CardContent } from '@mui/material';
import { Store, Receipt, Payments, TrendingUp } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { fetchMerchants } from '../services/merchantService';
import { fetchSettlements } from '../services/settlementService';
import { fetchEodStatus } from '../services/eodService';

function StatCard({ title, value, icon, color }: any) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography color="text.secondary" variant="overline">{title}</Typography>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>{value}</Typography>
          </Box>
          <Box sx={{ bgcolor: color, borderRadius: 2, p: 1, display: 'flex' }}>{icon}</Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { data: merchants } = useQuery({
    queryKey: ['merchants', 'dashboard'],
    queryFn: () => fetchMerchants({ page_size: 5 }),
  });

  const { data: settlements } = useQuery({
    queryKey: ['settlements', 'dashboard'],
    queryFn: () => fetchSettlements({ page_size: 1 }),
  });

  const { data: eodStatus } = useQuery({
    queryKey: ['eod-status', 'dashboard'],
    queryFn: fetchEodStatus,
    refetchInterval: 15000,
  });

  const activeCount = merchants?.data?.filter((m: any) => m.status === 'APPROVED').length ?? '—';

  const stats = [
    { title: 'Active Merchants', value: activeCount, icon: <Store sx={{ color: '#fff' }} />, color: '#1976d2' },
    { title: 'Pending EOD Batches', value: eodStatus?.pending ?? '—', icon: <Receipt sx={{ color: '#fff' }} />, color: '#388e3c' },
    { title: 'EOD In Progress', value: eodStatus?.in_progress ?? '—', icon: <Payments sx={{ color: '#fff' }} />, color: '#f57c00' },
    { title: 'EOD Failed', value: eodStatus?.failed ?? '—', icon: <TrendingUp sx={{ color: '#fff' }} />, color: '#7b1fa2' },
  ];

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Dashboard</Typography>
      <Grid container spacing={3}>
        {stats.map((stat) => (
          <Grid xs={12} sm={6} md={3} key={stat.title}>
            <StatCard {...stat} />
          </Grid>
        ))}
        <Grid xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Recent Merchants</Typography>
            {merchants?.data?.length ? (
              merchants.data.map((m: any) => (
                <Box key={m.merchant_id} sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: '1px solid #eee' }}>
                  <Typography>{m.business_name}</Typography>
                  <Typography color="text.secondary">{m.status}</Typography>
                </Box>
              ))
            ) : (
              <Typography color="text.secondary">No merchants yet</Typography>
            )}
          </Paper>
        </Grid>
        <Grid xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>System Health</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Typography variant="body2">Auth Service: <b>Healthy</b></Typography>
              <Typography variant="body2">Staging Queue: <b>{eodStatus?.pending || 0} pending</b></Typography>
              <Typography variant="body2">EOD Batch: <b>{eodStatus?.in_progress ? 'Running' : 'Idle'}</b></Typography>
              <Typography variant="body2">Merchants: <b>{merchants?.pagination?.total || 0} total</b></Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
