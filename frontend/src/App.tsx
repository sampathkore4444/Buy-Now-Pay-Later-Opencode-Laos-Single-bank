import { Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import DashboardPage from './pages/DashboardPage';
import MerchantsPage from './pages/MerchantsPage';
import MerchantDetailPage from './pages/MerchantDetailPage';
import TransactionsPage from './pages/TransactionsPage';
import SettlementPage from './pages/SettlementPage';
import LoginPage from './pages/LoginPage';
import EodPage from './pages/EodPage';
import ReconciliationPage from './pages/ReconciliationPage';
import MerchantHealthPage from './pages/MerchantHealthPage';
import ConsumersPage from './pages/ConsumersPage';
import StagingPage from './pages/StagingPage';
import WebhooksPage from './pages/WebhooksPage';
import FraudRulesPage from './pages/FraudRulesPage';
import OverdueTrackerPage from './pages/OverdueTrackerPage';
import NotificationLogsPage from './pages/NotificationLogsPage';
import CreditRefreshLogsPage from './pages/CreditRefreshLogsPage';

const theme = createTheme({
  palette: {
    primary: { main: '#1976d2' },
    secondary: { main: '#dc004e' },
    background: { default: '#f5f5f5' },
  },
  typography: {
    fontFamily: '"Roboto", "Noto Sans Lao", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<DashboardPage />} />
            <Route path="merchants" element={<MerchantsPage />} />
            <Route path="merchants/:merchantId" element={<MerchantDetailPage />} />
            <Route path="transactions" element={<TransactionsPage />} />
            <Route path="settlements" element={<SettlementPage />} />
            <Route path="eod" element={<EodPage />} />
            <Route path="reconciliation" element={<ReconciliationPage />} />
            <Route path="merchant-health" element={<MerchantHealthPage />} />
            <Route path="consumers" element={<ConsumersPage />} />
            <Route path="staging" element={<StagingPage />} />
            <Route path="webhooks" element={<WebhooksPage />} />
            <Route path="fraud-rules" element={<FraudRulesPage />} />
            <Route path="overdue" element={<OverdueTrackerPage />} />
            <Route path="notifications" element={<NotificationLogsPage />} />
            <Route path="credit-refresh" element={<CreditRefreshLogsPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
