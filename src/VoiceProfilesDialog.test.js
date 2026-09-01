import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import VoiceProfilesDialog from './VoiceProfilesDialog';
import i18n from 'i18next';
import { I18nextProvider, initReactI18next } from 'react-i18next';

if (!i18n.isInitialized) {
  i18n.use(initReactI18next).init({
    lng: 'en',
    fallbackLng: 'en',
    resources: { en: { translation: {} } }
  });
}

beforeEach(() => {
  const fetchMock = jest.fn((url, options) => {
    const urlStr = String(url);
    if (urlStr.includes('/tts/providers')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          local_dia: { id: 'local_dia', name: 'Local Dia', type: 'local', languages: [], voices: [] },
          azure: { id: 'azure', name: 'Azure Cognitive Services', type: 'cloud', languages: [], voices: [] }
        })
      });
    }
    if (urlStr.includes('/voice-profiles')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([
          { id: 'default_dia', name: 'Default Dia Profile', provider: 'local_dia', voice_id: 'dia-default', language: 'en-US', user: 'system', is_default: true },
          { id: 'azure_news', name: 'Azure News Anchor', provider: 'azure', voice_id: 'en-US-JennyNeural', language: 'en-US', user: 'system', is_default: false }
        ])
      });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  });
  global.fetch = fetchMock;
  window.fetch = fetchMock;
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe('VoiceProfilesDialog', () => {
  it('renders dialog when open and lists voice profiles', async () => {
    render(
      <I18nextProvider i18n={i18n}>
        <VoiceProfilesDialog open={true} onClose={() => {}} apiUrl="http://localhost:8000" />
      </I18nextProvider>
    );

    expect(global.fetch).toHaveBeenCalled();

    await waitFor(() => {
      expect(within(document.body).getByText('Default Dia Profile')).toBeInTheDocument();
      expect(within(document.body).getByText('Azure News Anchor')).toBeInTheDocument();
    });
  });

  it('switches to create profile mode when Create Profile button is clicked', async () => {
    render(
      <I18nextProvider i18n={i18n}>
        <VoiceProfilesDialog open={true} onClose={() => {}} apiUrl="http://localhost:8000" />
      </I18nextProvider>
    );

    await waitFor(() => {
      expect(within(document.body).getByText('Default Dia Profile')).toBeInTheDocument();
    });

    const createBtn = within(document.body).getByText(/\+ Create Profile/i);
    fireEvent.click(createBtn);

    await waitFor(() => {
      expect(within(document.body).getByText('Create Voice Profile')).toBeInTheDocument();
    });
    expect(within(document.body).getByLabelText(/Profile Name/i)).toBeInTheDocument();
  });
});
