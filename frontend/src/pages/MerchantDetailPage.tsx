import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Chip,
  Button,
  Card,
  CardContent,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { fetchMerchant } from '../services/merchantService';

export default function MerchantDetailPage() {
  const { merchantId } = useParams<{ merchantId: string }>();
  const navigate = useNavigate();

  const { data: merchant, isLoading } = useQuery({
    queryKey: ['merchant', merchantId],
    queryFn: () => fetchMerchant(merchantId!),
    enabled: !!merchantId,
  });

  if (isLoading) return <Typography>Loading...</Typography>;
  if (!merchant) return <Typography>Merchant not found</Typography>;

  return (
    <Box>
      <Button startIcon={<ArrowBack />} onClick={() => navigate('/merchants')} sx={{ mb: 2 }}>
        Back to Merchants
      </Button>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>
        {merchant.business_name}
      </Typography>

      <Grid container spacing={3}>
        <Grid xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Merchant Details</Typography>
              <DetailRow label="Merchant ID" value={merchant.merchant_id} />
              <DetailRow label="Status" value={<Chip label={merchant.status} color={merchant.status === 'APPROVED' ? 'success' : 'warning'} size="small" />} />
              <DetailRow label="Risk Tier" value={<Chip label={merchant.risk_tier} color={merchant.risk_tier === 'GREEN' ? 'success' : 'warning'} size="small" />} />
              <DetailRow label="MDR Rate" value={`${(merchant.mdr_rate * 100).toFixed(1)}%`} />
              <DetailRow label="Settlement Terms" value={merchant.settlement_terms} />
              <DetailRow label="Channels" value={merchant.channels?.join(', ')} />
            </CardContent>
          </Card>
        </Grid>
        <Grid xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Limits</Typography>
              <DetailRow label="Daily Limit" value={merchant.daily_limit_lak ? `${(merchant.daily_limit_lak / 1_000_000).toFixed(1)}M LAK` : 'N/A'} />
              <DetailRow label="Monthly Limit" value={merchant.monthly_limit_lak ? `${(merchant.monthly_limit_lak / 1_000_000).toFixed(1)}M LAK` : 'N/A'} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

function DetailRow({ label, value }: { label: string; value: any }) {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: '1px solid #eee' }}>
      <Typography color="text.secondary">{label}</Typography>
      <Typography sx={{ fontWeight: 500 }}>{value}</Typography>
    </Box>
  );
}
