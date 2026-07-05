import { Box, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, TablePagination, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField } from '@mui/material';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchComplaints, resolveComplaint } from '../services/complaintService';

export default function ComplaintsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);
  const [statusFilter, setStatusFilter] = useState<string>('OPEN');
  const [resolveDialog, setResolveDialog] = useState<string | null>(null);
  const [resolution, setResolution] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['complaints', page, rowsPerPage, statusFilter],
    queryFn: () => fetchComplaints({ page: page + 1, page_size: rowsPerPage, status: statusFilter || undefined }),
  });

  const resolveMutation = useMutation({
    mutationFn: ({ id, resolution }: { id: string; resolution: string }) => resolveComplaint(id, { resolution }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['complaints'] });
      setResolveDialog(null);
      setResolution('');
    },
  });

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>Consumer Complaints</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {['', 'OPEN', 'RESOLVED'].map((s) => (
            <Button key={s || 'all'} variant={statusFilter === s ? 'contained' : 'outlined'} size="small" onClick={() => { setStatusFilter(s); setPage(0); }}>
              {s || 'All'}
            </Button>
          ))}
        </Box>
      </Box>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Complaint ID</TableCell>
              <TableCell>Consumer</TableCell>
              <TableCell>Subject</TableCell>
              <TableCell>Channel</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.data?.map((c: any) => (
              <TableRow key={c.complaint_id}>
                <TableCell><Typography variant="body2" sx={{ fontFamily: 'monospace' }}>{c.complaint_id}</Typography></TableCell>
                <TableCell>{c.consumer_id}</TableCell>
                <TableCell>{c.subject}</TableCell>
                <TableCell><Chip label={c.channel} size="small" /></TableCell>
                <TableCell><Chip label={c.status} color={c.status === 'OPEN' ? 'warning' : 'success'} size="small" /></TableCell>
                <TableCell>{c.created_at ? new Date(c.created_at).toLocaleString() : '—'}</TableCell>
                <TableCell>
                  {c.status === 'OPEN' && (
                    <Button size="small" variant="outlined" onClick={() => setResolveDialog(c.complaint_id)}>Resolve</Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {!data?.data?.length && !isLoading && (
              <TableRow><TableCell colSpan={7} align="center">No complaints found</TableCell></TableRow>
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

      <Dialog open={!!resolveDialog} onClose={() => setResolveDialog(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Resolve Complaint</DialogTitle>
        <DialogContent>
          <TextField label="Resolution Notes" multiline rows={4} fullWidth sx={{ mt: 2 }} value={resolution} onChange={(e) => setResolution(e.target.value)} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResolveDialog(null)}>Cancel</Button>
          <Button variant="contained" onClick={() => resolveDialog && resolveMutation.mutate({ id: resolveDialog, resolution })}>Resolve</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
