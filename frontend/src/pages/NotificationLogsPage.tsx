import { Box, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, TablePagination, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchNotifications } from '../services/notificationService';

export default function NotificationLogsPage() {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);
  const [channelFilter, setChannelFilter] = useState<string>('');

  const { data, isLoading } = useQuery({
    queryKey: ['notifications', page, rowsPerPage, channelFilter],
    queryFn: () => fetchNotifications({ page: page + 1, page_size: rowsPerPage, channel: channelFilter || undefined }),
  });

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3, alignItems: 'center' }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>Notification Logs</Typography>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Channel</InputLabel>
          <Select value={channelFilter} label="Channel" onChange={(e) => { setChannelFilter(e.target.value); setPage(0); }}>
            <MenuItem value="">All</MenuItem>
            <MenuItem value="SMS">SMS</MenuItem>
            <MenuItem value="EMAIL">Email</MenuItem>
            <MenuItem value="PUSH">Push</MenuItem>
          </Select>
        </FormControl>
      </Box>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Notification ID</TableCell>
              <TableCell>Recipient</TableCell>
              <TableCell>Channel</TableCell>
              <TableCell>Template</TableCell>
              <TableCell>Message</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Sent At</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.data?.map((log: any) => (
              <TableRow key={log.notification_id}>
                <TableCell><Typography variant="body2" sx={{ fontFamily: 'monospace' }}>{log.notification_id}</Typography></TableCell>
                <TableCell>{log.recipient}</TableCell>
                <TableCell><Chip label={log.channel} size="small" /></TableCell>
                <TableCell><Chip label={log.template} size="small" variant="outlined" /></TableCell>
                <TableCell><Typography variant="body2" sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{log.message}</Typography></TableCell>
                <TableCell><Chip label={log.status} color={log.status === 'SENT' ? 'success' : 'warning'} size="small" /></TableCell>
                <TableCell>{log.sent_at ? new Date(log.sent_at).toLocaleString() : '—'}</TableCell>
              </TableRow>
            ))}
            {!data?.data?.length && !isLoading && (
              <TableRow><TableCell colSpan={7} align="center">No notification logs</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={data?.pagination?.total || 0}
          page={page}
          onPageChange={(_, p) => setPage(p)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }}
        />
      </TableContainer>
    </Box>
  );
}
