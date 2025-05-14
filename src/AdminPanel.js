import React, { useState, useEffect } from 'react';
import { Box, Typography, Tabs, Tab, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button, TextField, Dialog, DialogTitle, DialogContent, DialogActions, Snackbar, Alert } from '@mui/material';
import { useTranslation } from 'react-i18next';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function AdminPanel() {
  const { t } = useTranslation();
  const [tab, setTab] = useState(0);
  const [users, setUsers] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [auditLog, setAuditLog] = useState([]);
  const [editUser, setEditUser] = useState(null);
  const [showMsg, setShowMsg] = useState(false);
  const [msg, setMsg] = useState('');
  const [msgType, setMsgType] = useState('info');

  useEffect(() => {
    if (tab === 0) fetchUsers();
    if (tab === 1) fetchTenants();
    if (tab === 2) fetchAuditLog();
    // eslint-disable-next-line
  }, [tab]);

  const fetchUsers = async () => {
    const resp = await fetch(`${API_URL}/admin/users`, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
    const data = await resp.json();
    setUsers(data.users || []);
  };
  const fetchTenants = async () => {
    const resp = await fetch(`${API_URL}/admin/tenants`, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
    const data = await resp.json();
    setTenants(data.tenants || []);
  };
  const fetchAuditLog = async () => {
    const resp = await fetch(`${API_URL}/admin/audit-log`, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
    const data = await resp.json();
    setAuditLog(data.audit_log || []);
  };

  const handleEditUser = (user) => setEditUser(user);
  const handleCloseEdit = () => setEditUser(null);
  const handleSaveUser = async () => {
    const method = editUser.id ? 'PUT' : 'POST';
    const url = editUser.id ? `${API_URL}/admin/users/${editUser.id}` : `${API_URL}/admin/users`;
    const resp = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token')}` },
      body: JSON.stringify(editUser)
    });
    if (resp.ok) {
      setMsg(t('User saved'));
      setMsgType('success');
      setShowMsg(true);
      fetchUsers();
      setEditUser(null);
    } else {
      setMsg(t('Failed to save user'));
      setMsgType('error');
      setShowMsg(true);
    }
  };
  const handleDeleteUser = async (id) => {
    if (!window.confirm(t('Delete this user?'))) return;
    const resp = await fetch(`${API_URL}/admin/users/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    });
    if (resp.ok) {
      setMsg(t('User deleted'));
      setMsgType('success');
      setShowMsg(true);
      fetchUsers();
    } else {
      setMsg(t('Failed to delete user'));
      setMsgType('error');
      setShowMsg(true);
    }
  };

  return (
    <Box mt={4}>
      <Typography variant="h5" sx={{ mb: 2 }}>{t('Admin Panel')}</Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} aria-label="admin panel tabs" role="tablist">
        <Tab label={t('Users')} id="admin-tab-users" aria-controls="admin-tabpanel-users" role="tab" />
        <Tab label={t('Tenants')} id="admin-tab-tenants" aria-controls="admin-tabpanel-tenants" role="tab" />
        <Tab label={t('Audit Log')} id="admin-tab-audit" aria-controls="admin-tabpanel-audit" role="tab" />
      </Tabs>
      {tab === 0 && (
        <Box mt={2} id="admin-tabpanel-users" role="tabpanel" aria-labelledby="admin-tab-users">
          <Button variant="contained" onClick={() => setEditUser({ username: '', role: 'user', tenant: '' })}>{t('Add User')}</Button>
          <TableContainer component={Paper} sx={{ mt: 2 }}>
            <Table size="small" aria-label={t('Users')} role="table">
              <TableHead>
                <TableRow>
                  <TableCell>{t('Username')}</TableCell>
                  <TableCell>{t('Role')}</TableCell>
                  <TableCell>{t('Tenant')}</TableCell>
                  <TableCell>{t('Actions')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map(user => (
                  <TableRow key={user.id} tabIndex={0} aria-label={user.username}>
                    <TableCell>{user.username}</TableCell>
                    <TableCell>{user.role}</TableCell>
                    <TableCell>{user.tenant}</TableCell>
                    <TableCell>
                      <Button size="small" onClick={() => handleEditUser(user)} aria-label={t('Edit')}>{t('Edit')}</Button>
                      <Button size="small" color="error" onClick={() => handleDeleteUser(user.id)} aria-label={t('Delete')}>{t('Delete')}</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <Dialog open={!!editUser} onClose={handleCloseEdit} aria-labelledby="edit-user-dialog-title">
            <DialogTitle id="edit-user-dialog-title">{editUser && editUser.id ? t('Edit User') : t('Add User')}</DialogTitle>
            <DialogContent>
              <TextField label={t('Username')} value={editUser?.username || ''} onChange={e => setEditUser(u => ({ ...u, username: e.target.value }))} fullWidth sx={{ mb: 2 }} inputProps={{ 'aria-label': t('Username') }} />
              <TextField label={t('Role')} value={editUser?.role || ''} onChange={e => setEditUser(u => ({ ...u, role: e.target.value }))} fullWidth sx={{ mb: 2 }} inputProps={{ 'aria-label': t('Role') }} />
              <TextField label={t('Tenant')} value={editUser?.tenant || ''} onChange={e => setEditUser(u => ({ ...u, tenant: e.target.value }))} fullWidth sx={{ mb: 2 }} inputProps={{ 'aria-label': t('Tenant') }} />
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseEdit} aria-label={t('Cancel')}>{t('Cancel')}</Button>
              <Button onClick={handleSaveUser} variant="contained" aria-label={t('Save')}>{t('Save')}</Button>
            </DialogActions>
          </Dialog>
        </Box>
      )}
      {tab === 1 && (
        <Box mt={2} id="admin-tabpanel-tenants" role="tabpanel" aria-labelledby="admin-tab-tenants">
          <TableContainer component={Paper}>
            <Table size="small" aria-label={t('Tenants')} role="table">
              <TableHead>
                <TableRow>
                  <TableCell>{t('Tenant')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {tenants.map(tenant => (
                  <TableRow key={tenant} tabIndex={0} aria-label={tenant}>
                    <TableCell>{tenant}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}
      {tab === 2 && (
        <Box mt={2} id="admin-tabpanel-audit" role="tabpanel" aria-labelledby="admin-tab-audit">
          <TableContainer component={Paper}>
            <Table size="small" aria-label={t('Audit Log')} role="table">
              <TableHead>
                <TableRow>
                  <TableCell>{t('Timestamp')}</TableCell>
                  <TableCell>{t('User')}</TableCell>
                  <TableCell>{t('Action')}</TableCell>
                  <TableCell>{t('Details')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {auditLog.map((log, idx) => (
                  <TableRow key={idx} tabIndex={0} aria-label={log.user}>
                    <TableCell>{log.timestamp}</TableCell>
                    <TableCell>{log.user}</TableCell>
                    <TableCell>{log.action}</TableCell>
                    <TableCell>{log.details}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}
      <Snackbar open={showMsg} autoHideDuration={4000} onClose={() => setShowMsg(false)}>
        <Alert onClose={() => setShowMsg(false)} severity={msgType} sx={{ width: '100%' }}>
          {msg}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default AdminPanel;
