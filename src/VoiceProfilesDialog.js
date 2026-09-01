import React, { useState, useEffect } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  FormControl, InputLabel, Select, MenuItem, TextField, Switch,
  FormControlLabel, Box, Typography, Table, TableBody, TableCell,
  TableHead, TableRow, Chip, Alert, Card, CardContent, Divider
} from '@mui/material';
import { useTranslation } from 'react-i18next';

export const DEFAULT_PROVIDERS = {
  local_dia: {
    id: 'local_dia',
    name: 'Local Dia (On-Device)',
    type: 'local',
    supports_ssml: false,
    supported_formats: ['wav', 'mp3', 'ogg'],
    languages: [{ code: 'en-US', name: 'English (US)' }, { code: 'es-ES', name: 'Spanish' }],
    voices: [
      { id: 'dia-default', name: 'Dia Voice 1 (Default)', gender: 'neutral' },
      { id: 'dia-female', name: 'Dia Voice 2 (Female)', gender: 'female' },
      { id: 'dia-male', name: 'Dia Voice 3 (Male)', gender: 'male' }
    ]
  },
  azure: {
    id: 'azure',
    name: 'Azure Cognitive Services Speech',
    type: 'cloud',
    supports_ssml: true,
    supported_formats: ['wav', 'mp3', 'ogg', 'pcm'],
    languages: [
      { code: 'en-US', name: 'English (US)' },
      { code: 'fr-FR', name: 'French' },
      { code: 'de-DE', name: 'German' },
      { code: 'es-ES', name: 'Spanish' }
    ],
    voices: [
      { id: 'en-US-JennyNeural', name: 'Jenny (Neural)', gender: 'female', styles: ['cheerful', 'sad', 'empathetic', 'chat', 'newscast'] },
      { id: 'en-US-GuyNeural', name: 'Guy (Neural)', gender: 'male', styles: ['newscast', 'angry', 'cheerful'] }
    ]
  },
  aws: {
    id: 'aws',
    name: 'AWS Polly',
    type: 'cloud',
    supports_ssml: true,
    supported_formats: ['mp3', 'ogg', 'pcm', 'wav'],
    languages: [{ code: 'en-US', name: 'English (US)' }, { code: 'es-US', name: 'Spanish (US)' }],
    voices: [
      { id: 'Joanna', name: 'Joanna', gender: 'female', engines: ['standard', 'neural'] },
      { id: 'Matthew', name: 'Matthew', gender: 'male', engines: ['standard', 'neural', 'generative'] }
    ]
  },
  google: {
    id: 'google',
    name: 'Google Cloud Text-to-Speech',
    type: 'cloud',
    supports_ssml: true,
    supported_formats: ['mp3', 'wav', 'ogg'],
    languages: [{ code: 'en-US', name: 'English (US)' }, { code: 'ja-JP', name: 'Japanese' }],
    voices: [
      { id: 'en-US-Neural2-F', name: 'Neural2 Female F', gender: 'female' },
      { id: 'en-US-Studio-O', name: 'Studio Male O', gender: 'male' }
    ]
  }
};

const initialForm = {
  name: '',
  description: '',
  provider: 'local_dia',
  voice_id: 'dia-default',
  language: 'en-US',
  gender: 'neutral',
  is_default: false,
  settings: {
    speaking_rate: 1.0,
    pitch: 0.0,
    volume: 100.0,
    output_format: 'wav',
    sample_rate: 22050
  },
  provider_params: {},
  fallback_config: {
    allow_provider_fallback: true,
    fallback_provider: 'local_dia'
  }
};

function VoiceProfilesDialog({ open, onClose, token, apiUrl, onSelectProfile, currentProfileId }) {
  const { t } = useTranslation();
  const [profiles, setProfiles] = useState([]);
  const [providers, setProviders] = useState(DEFAULT_PROVIDERS);
  const [editingProfile, setEditingProfile] = useState(null);
  const [formData, setFormData] = useState(initialForm);
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'form'
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    if (open) {
      fetchProviders();
      fetchProfiles();
    }
  }, [open, token, apiUrl]);

  const fetchProviders = async () => {
    try {
      const res = await fetch(`${apiUrl}/tts/providers`);
      if (res.ok) {
        const data = await res.json();
        setProviders(data.providers || data);
      }
    } catch {
      // Use defaults if fetch fails
      setProviders(DEFAULT_PROVIDERS);
    }
  };

  const fetchProfiles = async () => {
    try {
      const headers = token ? { 'Authorization': 'Bearer ' + token } : {};
      const res = await fetch(`${apiUrl}/voice-profiles`, { headers });
      if (res.ok) {
        const data = await res.json();
        setProfiles(Array.isArray(data) ? data : (data.profiles || []));
      }
    } catch (e) {
      console.log('fetchProfiles err:', e);
      setError(t('Failed to load voice profiles'));
    }
  };

  const handleOpenForm = (profile = null) => {
    setError(null);
    setSuccess(null);
    if (profile) {
      setEditingProfile(profile);
      setFormData({
        name: profile.name || '',
        description: profile.description || '',
        provider: profile.provider || 'local_dia',
        voice_id: profile.voice_id || '',
        language: profile.language || 'en-US',
        gender: profile.gender || 'neutral',
        is_default: profile.is_default || false,
        settings: {
          speaking_rate: profile.settings?.speaking_rate ?? 1.0,
          pitch: profile.settings?.pitch ?? 0.0,
          volume: profile.settings?.volume ?? 100.0,
          output_format: profile.settings?.output_format || 'wav',
          sample_rate: profile.settings?.sample_rate || 22050
        },
        provider_params: profile.provider_params || {},
        fallback_config: {
          allow_provider_fallback: profile.fallback_config?.allow_provider_fallback ?? true,
          fallback_provider: profile.fallback_config?.fallback_provider || 'local_dia'
        }
      });
    } else {
      setEditingProfile(null);
      setFormData(initialForm);
    }
    setViewMode('form');
  };

  const handleProviderChange = (e) => {
    const pKey = e.target.value;
    const pCap = providers[pKey] || DEFAULT_PROVIDERS[pKey];
    const defaultVoice = pCap?.voices?.[0]?.id || '';
    const defaultLang = pCap?.languages?.[0]?.code || 'en-US';

    setFormData(prev => ({
      ...prev,
      provider: pKey,
      voice_id: defaultVoice,
      language: defaultLang,
      settings: {
        ...prev.settings,
        output_format: pCap?.supported_formats?.[0] || 'wav'
      }
    }));
  };

  const handleSave = async () => {
    setError(null);
    if (!formData.name.trim()) {
      setError(t('Profile name is required'));
      return;
    }
    try {
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': 'Bearer ' + token } : {})
      };
      const url = editingProfile
        ? `${apiUrl}/voice-profiles/${editingProfile.id}`
        : `${apiUrl}/voice-profiles`;
      const method = editingProfile ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method,
        headers,
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.message || data.error || 'Failed to save profile');
      }

      setSuccess(editingProfile ? t('Profile updated successfully') : t('Profile created successfully'));
      fetchProfiles();
      setViewMode('list');
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm(t('Are you sure you want to delete this profile?'))) return;
    try {
      const headers = token ? { 'Authorization': 'Bearer ' + token } : {};
      const res = await fetch(`${apiUrl}/voice-profiles/${id}`, { method: 'DELETE', headers });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.message || data.error || 'Failed to delete');
      }
      setSuccess(t('Profile deleted'));
      fetchProfiles();
    } catch (err) {
      setError(err.message);
    }
  };

  const selectedProviderCap = providers[formData.provider] || DEFAULT_PROVIDERS[formData.provider];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth disablePortal aria-labelledby="voice-profiles-dialog-title">
      <DialogTitle id="voice-profiles-dialog-title">
        {t('Voice Profiles & Provider Configuration')}
      </DialogTitle>
      <DialogContent dividers>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

        {viewMode === 'list' && (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, alignItems: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                {t('Configure voice profiles for on-device TTS and cloud providers (Azure, AWS, Google).')}
              </Typography>
              <Button variant="contained" color="primary" onClick={() => handleOpenForm()}>
                + {t('Create Profile')}
              </Button>
            </Box>

            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t('Name')}</TableCell>
                  <TableCell>{t('Provider')}</TableCell>
                  <TableCell>{t('Voice ID')}</TableCell>
                  <TableCell>{t('Language')}</TableCell>
                  <TableCell>{t('Status')}</TableCell>
                  <TableCell align="right">{t('Actions')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {profiles.map(p => (
                  <TableRow key={p.id} selected={p.id === currentProfileId}>
                    <TableCell>
                      <Typography variant="subtitle2">{p.name}</Typography>
                      {p.description && <Typography variant="caption" color="text.secondary">{p.description}</Typography>}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={p.provider}
                        size="small"
                        color={(p.provider || '').includes('azure') || (p.provider || '').includes('aws') || (p.provider || '').includes('google') ? 'info' : 'secondary'}
                      />
                    </TableCell>
                    <TableCell>{p.voice_id}</TableCell>
                    <TableCell>{p.language}</TableCell>
                    <TableCell>
                      {p.is_default && <Chip label={t('Default')} size="small" color="success" sx={{ mr: 0.5 }} />}
                      {p.user === 'system' && <Chip label={t('System')} size="small" variant="outlined" />}
                    </TableCell>
                    <TableCell align="right">
                      {onSelectProfile && (
                        <Button size="small" sx={{ mr: 1 }} onClick={() => { onSelectProfile(p.id); onClose(); }}>
                          {t('Select')}
                        </Button>
                      )}
                      <Button size="small" sx={{ mr: 1 }} onClick={() => handleOpenForm(p)}>
                        {t('Edit')}
                      </Button>
                      {p.user !== 'system' && (
                        <Button size="small" color="error" onClick={() => handleDelete(p.id)}>
                          {t('Delete')}
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        )}

        {viewMode === 'form' && (
          <Box component="form" sx={{ mt: 1 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              {editingProfile ? t('Edit Voice Profile') : t('Create Voice Profile')}
            </Typography>

            <TextField
              label={t('Profile Name')}
              fullWidth
              value={formData.name}
              onChange={e => setFormData({ ...formData, name: e.target.value })}
              sx={{ mb: 2 }}
            />

            <TextField
              label={t('Description')}
              fullWidth
              multiline
              rows={2}
              value={formData.description}
              onChange={e => setFormData({ ...formData, description: e.target.value })}
              sx={{ mb: 2 }}
            />

            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  {t('Provider & Voice Selection')}
                </Typography>
                
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>{t('TTS Provider')}</InputLabel>
                  <Select value={formData.provider} label={t('TTS Provider')} onChange={handleProviderChange}>
                    {Object.keys(providers).map(pk => (
                      <MenuItem key={pk} value={pk}>
                        {providers[pk]?.name || pk} ({providers[pk]?.type || 'local'})
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>{t('Language')}</InputLabel>
                  <Select
                    value={formData.language}
                    label={t('Language')}
                    onChange={e => setFormData({ ...formData, language: e.target.value })}
                  >
                    {(selectedProviderCap?.languages || [{ code: 'en-US', name: 'English (US)' }]).map(l => (
                      <MenuItem key={l.code} value={l.code}>{l.name} ({l.code})</MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>{t('Voice')}</InputLabel>
                  <Select
                    value={formData.voice_id}
                    label={t('Voice')}
                    onChange={e => setFormData({ ...formData, voice_id: e.target.value })}
                  >
                    {(selectedProviderCap?.voices || []).map(v => (
                      <MenuItem key={v.id} value={v.id}>
                        {v.name} ({v.gender || 'neutral'})
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </CardContent>
            </Card>

            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  {t('Voice Tuning & Settings')}
                </Typography>

                <TextField
                  label={t('Speaking Rate (0.25 - 4.0)')}
                  type="number"
                  inputProps={{ step: 0.1, min: 0.25, max: 4.0 }}
                  value={formData.settings.speaking_rate}
                  onChange={e => setFormData({
                    ...formData,
                    settings: { ...formData.settings, speaking_rate: parseFloat(e.target.value) || 1.0 }
                  })}
                  fullWidth
                  sx={{ mb: 2 }}
                />

                <TextField
                  label={t('Pitch (-20 to 20)')}
                  type="number"
                  inputProps={{ step: 0.5, min: -20, max: 20 }}
                  value={formData.settings.pitch}
                  onChange={e => setFormData({
                    ...formData,
                    settings: { ...formData.settings, pitch: parseFloat(e.target.value) || 0.0 }
                  })}
                  fullWidth
                  sx={{ mb: 2 }}
                />

                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>{t('Output Format')}</InputLabel>
                  <Select
                    value={formData.settings.output_format}
                    label={t('Output Format')}
                    onChange={e => setFormData({
                      ...formData,
                      settings: { ...formData.settings, output_format: e.target.value }
                    })}
                  >
                    {(selectedProviderCap?.supported_formats || ['wav', 'mp3', 'ogg']).map(fmt => (
                      <MenuItem key={fmt} value={fmt}>{fmt.toUpperCase()}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </CardContent>
            </Card>

            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  {t('Fallback Configuration')}
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.fallback_config.allow_provider_fallback}
                      onChange={e => setFormData({
                        ...formData,
                        fallback_config: { ...formData.fallback_config, allow_provider_fallback: e.target.checked }
                      })}
                    />
                  }
                  label={t('Allow fallback to local/backup provider on error or rate limit')}
                />
              </CardContent>
            </Card>

            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_default}
                  onChange={e => setFormData({ ...formData, is_default: e.target.checked })}
                />
              }
              label={t('Set as Default Voice Profile')}
            />
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        {viewMode === 'form' ? (
          <>
            <Button onClick={() => setViewMode('list')}>{t('Back to List')}</Button>
            <Button variant="contained" onClick={handleSave}>{t('Save Profile')}</Button>
          </>
        ) : (
          <Button onClick={onClose}>{t('Close')}</Button>
        )}
      </DialogActions>
    </Dialog>
  );
}

export default VoiceProfilesDialog;
