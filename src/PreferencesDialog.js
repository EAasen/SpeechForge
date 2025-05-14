import React, { useState, useEffect } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, FormControl, InputLabel, Select, MenuItem, TextField, Switch, FormControlLabel } from '@mui/material';
import { useTranslation } from 'react-i18next';

const defaultPrefs = {
  language: 'en',
  theme: 'light',
  voice: 'default',
  speed: '',
  pitch: '',
  tone: '',
};

function PreferencesDialog({ open, onClose, onSave, prefs }) {
  const { t, i18n } = useTranslation();
  const [values, setValues] = useState(defaultPrefs);
  const [notify, setNotify] = useState(() => {
    try { return JSON.parse(localStorage.getItem('notifyOnJob') || 'false'); } catch { return false; }
  });

  useEffect(() => {
    setValues({ ...defaultPrefs, ...prefs });
    setNotify(prefs.notifyOnJob || false);
  }, [prefs]);

  const handleChange = (e) => {
    setValues(v => ({ ...v, [e.target.name]: e.target.value }));
  };
  const handleTheme = (e) => {
    setValues(v => ({ ...v, theme: e.target.checked ? 'dark' : 'light' }));
  };
  const handleNotifyChange = (e) => {
    setNotify(e.target.checked);
    onSave({ ...prefs, notifyOnJob: e.target.checked });
    localStorage.setItem('notifyOnJob', JSON.stringify(e.target.checked));
  };
  const handleSave = () => {
    onSave(values);
    if (values.language) i18n.changeLanguage(values.language);
  };

  return (
    <Dialog open={open} onClose={onClose} aria-labelledby="prefs-dialog-title">
      <DialogTitle id="prefs-dialog-title">{t('Preferences')}</DialogTitle>
      <DialogContent>
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>{t('Language')}</InputLabel>
          <Select name="language" value={values.language} label={t('Language')} onChange={handleChange}>
            {Object.keys(i18n.options.resources).map(lng => (
              <MenuItem key={lng} value={lng}>{lng}</MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControlLabel control={<Switch checked={values.theme === 'dark'} onChange={handleTheme} />} label={t('Dark Theme')} />
        <TextField label={t('Voice')} name="voice" value={values.voice} onChange={handleChange} fullWidth sx={{ mb: 2, mt: 2 }} />
        <TextField label={t('Speed')} name="speed" value={values.speed} onChange={handleChange} fullWidth sx={{ mb: 2 }} />
        <TextField label={t('Pitch')} name="pitch" value={values.pitch} onChange={handleChange} fullWidth sx={{ mb: 2 }} />
        <TextField label={t('Tone')} name="tone" value={values.tone} onChange={handleChange} fullWidth sx={{ mb: 2 }} />
        <FormControlLabel control={<Switch checked={notify} onChange={handleNotifyChange} />} label={t('Enable notifications for job completion')} />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t('Cancel')}</Button>
        <Button onClick={handleSave} variant="contained">{t('Save')}</Button>
      </DialogActions>
    </Dialog>
  );
}

export default PreferencesDialog;
