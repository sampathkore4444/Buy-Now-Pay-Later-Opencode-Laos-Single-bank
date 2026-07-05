import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Avatar,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard,
  Store,
  Receipt,
  Payment,
  Assignment,
  CompareArrows,
  HealthAndSafety,
  People,
  Storage,
  Webhook,
  Logout,
  Gavel,
  Warning,
  Notifications,
  Cached,
} from '@mui/icons-material';
import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

const drawerWidth = 260;

const navItems = [
  { label: 'Dashboard', path: '/', icon: <Dashboard /> },
  { label: 'Merchants', path: '/merchants', icon: <Store /> },
  { label: 'Merchant Health', path: '/merchant-health', icon: <HealthAndSafety /> },
  { label: 'Transactions', path: '/transactions', icon: <Receipt /> },
  { label: 'Settlements', path: '/settlements', icon: <Payment /> },
  { label: 'Consumers', path: '/consumers', icon: <People /> },
  { label: 'EOD Batch', path: '/eod', icon: <Assignment /> },
  { label: 'Reconciliation', path: '/reconciliation', icon: <CompareArrows /> },
  { label: 'Staging', path: '/staging', icon: <Storage /> },
  { label: 'Webhooks', path: '/webhooks', icon: <Webhook /> },
  { label: 'Fraud Rules', path: '/fraud-rules', icon: <Gavel /> },
  { label: 'Overdue', path: '/overdue', icon: <Warning /> },
  { label: 'Notifications', path: '/notifications', icon: <Notifications /> },
  { label: 'Credit Refresh', path: '/credit-refresh', icon: <Cached /> },
];

export default function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const drawer = (
    <Box>
      <Toolbar>
        <Typography variant="h6" noWrap sx={{ fontWeight: 700 }}>
          BNPL Portal
        </Typography>
      </Toolbar>
      <List>
        {navItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => {
                navigate(item.path);
                setMobileOpen(false);
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{ width: { md: `calc(100% - ${drawerWidth}px)` }, ml: { md: `${drawerWidth}px` } }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => setMobileOpen(!mobileOpen)}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap sx={{ flexGrow: 1 }}>
            Merchant Web Portal
          </Typography>
          <Typography variant="body2" sx={{ mr: 2 }}>{user?.name}</Typography>
          <Avatar
            sx={{ cursor: 'pointer', bgcolor: 'secondary.main' }}
            onClick={(e) => setAnchorEl(e.currentTarget)}
          >
            {user?.name?.charAt(0)?.toUpperCase() || 'A'}
          </Avatar>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={() => setAnchorEl(null)}
          >
            <MenuItem onClick={() => { setAnchorEl(null); logout(); navigate('/login'); }}>
              <Logout sx={{ mr: 1 }} /> Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>
      <Box component="nav" sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}>
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{ flexGrow: 1, p: 3, width: { md: `calc(100% - ${drawerWidth}px)` }, mt: 8 }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}
