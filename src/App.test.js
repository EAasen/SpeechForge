import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';
import i18n from 'i18next';
import { I18nextProvider } from 'react-i18next';

describe('App', () => {
  it('renders main UI and switches language', async () => {
    render(
      <I18nextProvider i18n={i18n}>
        <App />
      </I18nextProvider>
    );
    // Check for English title
    expect(screen.getByText(/DiaSpeak Web UI/i)).toBeInTheDocument();
    // Switch to Spanish
    userEvent.selectOptions(screen.getByLabelText(/Select language/i), 'es');
    // Use getAllByText to avoid multiple match error
    expect(await screen.findAllByText(/Iniciar sesión|Catálogo|Texto a voz/i)).not.toHaveLength(0);
    // Switch to Chinese
    userEvent.selectOptions(screen.getByLabelText(/Select language/i), 'zh');
    expect(await screen.findAllByText(/登录|目录|文本转语音/i)).not.toHaveLength(0);
  });
});
