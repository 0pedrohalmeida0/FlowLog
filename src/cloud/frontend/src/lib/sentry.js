// Sentry no frontend (v2.1, grátis).
// Requer: VITE_SENTRY_DSN no .env do frontend
// Setup: https://sentry.io → projeto Browser/JavaScript → pegar DSN

import * as Sentry from '@sentry/react'

const DSN = import.meta.env.VITE_SENTRY_DSN

export function initSentry() {
  if (!DSN) {
    console.info('ℹ️ Sentry não configurado (VITE_SENTRY_DSN vazio)')
    return
  }

  Sentry.init({
    dsn: DSN,
    environment: import.meta.env.MODE, // dev, staging, prod
    release: `flowlog-cloud-frontend@${import.meta.env.VITE_APP_VERSION || 'dev'}`,
    tracesSampleRate: 0.1,  // 10% das requisições
    replaysSessionSampleRate: 0.0,  // session replay off (privacidade)
    replaysOnErrorSampleRate: 0.5,  // 50% dos erros gravam replay
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
    ],
    // Filtra: tokens, senhas, etc
    beforeSend(event) {
      if (event.request?.headers) {
        delete event.request.headers.Authorization
      }
      return event
    },
  })
}
