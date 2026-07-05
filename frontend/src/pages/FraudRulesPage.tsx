import { useState } from 'react';
import {
  Box, Typography, Paper, Button, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Switch, IconButton, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, Select, MenuItem, FormControl, InputLabel, Chip
} from '@mui/material';
import { Add, Edit, Delete } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchFraudRules, createFraudRule, updateFraudRule, deleteFraudRule } from '../services/fraudRuleService';

export default function FraudRulesPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [editRule, setEditRule] = useState<any>(null);
  const [form, setForm] = useState({ rule_name: '', rule_type: '', parameter: '', threshold: '', action: 'BLOCK', enabled: true });

  const { data, isLoading } = useQuery({
    queryKey: ['fraud-rules'],
    queryFn: fetchFraudRules,
  });

  const createMutation = useMutation({
    mutationFn: createFraudRule,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['fraud-rules'] }); setOpen(false); resetForm(); },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: any }) => updateFraudRule(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['fraud-rules'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteFraudRule,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['fraud-rules'] }),
  });

  function resetForm() {
    setForm({ rule_name: '', rule_type: '', parameter: '', threshold: '', action: 'BLOCK', enabled: true });
    setEditRule(null);
  }

  function handleEdit(rule: any) {
    setEditRule(rule);
    setForm({ rule_name: rule.rule_name, rule_type: rule.rule_type, parameter: rule.parameter, threshold: rule.threshold, action: rule.action, enabled: rule.enabled });
    setOpen(true);
  }

  function handleSave() {
    if (editRule) {
      updateMutation.mutate({ id: editRule.id, payload: form });
    } else {
      createMutation.mutate(form);
    }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>Fraud Rules</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={() => { resetForm(); setOpen(true); }}>Add Rule</Button>
      </Box>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Rule Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Parameter</TableCell>
              <TableCell>Threshold</TableCell>
              <TableCell>Action</TableCell>
              <TableCell>Enabled</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.data?.map((rule: any) => (
              <TableRow key={rule.id}>
                <TableCell><Typography fontWeight={500}>{rule.rule_name}</Typography></TableCell>
                <TableCell><Chip label={rule.rule_type} size="small" /></TableCell>
                <TableCell>{rule.parameter}</TableCell>
                <TableCell>{rule.threshold}</TableCell>
                <TableCell><Chip label={rule.action} color={rule.action === 'BLOCK' ? 'error' : 'warning'} size="small" /></TableCell>
                <TableCell>
                  <Switch checked={rule.enabled} onChange={(e) => updateMutation.mutate({ id: rule.id, payload: { enabled: e.target.checked } })} />
                </TableCell>
                <TableCell>
                  <IconButton onClick={() => handleEdit(rule)}><Edit /></IconButton>
                  <IconButton onClick={() => deleteMutation.mutate(rule.id)} color="error"><Delete /></IconButton>
                </TableCell>
              </TableRow>
            ))}
            {!data?.data?.length && !isLoading && (
              <TableRow><TableCell colSpan={7} align="center">No fraud rules configured</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editRule ? 'Edit Rule' : 'Add Rule'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField label="Rule Name" value={form.rule_name} onChange={(e) => setForm({ ...form, rule_name: e.target.value })} disabled={!!editRule} />
            <FormControl>
              <InputLabel>Rule Type</InputLabel>
              <Select value={form.rule_type} label="Rule Type" onChange={(e) => setForm({ ...form, rule_type: e.target.value })}>
                <MenuItem value="THRESHOLD">Threshold</MenuItem>
                <MenuItem value="VELOCITY">Velocity</MenuItem>
                <MenuItem value="BLACKLIST">Blacklist</MenuItem>
                <MenuItem value="PATTERN">Pattern</MenuItem>
              </Select>
            </FormControl>
            <TextField label="Parameter" value={form.parameter} onChange={(e) => setForm({ ...form, parameter: e.target.value })} />
            <TextField label="Threshold" value={form.threshold} onChange={(e) => setForm({ ...form, threshold: e.target.value })} />
            <FormControl>
              <InputLabel>Action</InputLabel>
              <Select value={form.action} label="Action" onChange={(e) => setForm({ ...form, action: e.target.value })}>
                <MenuItem value="BLOCK">Block</MenuItem>
                <MenuItem value="FLAG">Flag</MenuItem>
                <MenuItem value="REVIEW">Review</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSave}>{editRule ? 'Update' : 'Create'}</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
