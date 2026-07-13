"""Sentry integration (v2.1 — grátis até 5k eventos/mês).

Setup:
    1. Criar conta grátis em https://sentry.io
    2. Criar projeto Python (FastAPI)
    3. Pegar o DSN (formato https://<key>@<org>.ingest.sentry.io/<project>)
    4. Setar SENTRY_DSN=<dsn> como env var (ou .env)

Como funciona:
    - init_sentry() é chamado no startup do FastAPI
    - Captura exceptions não tratadas automaticamente
    - NÃO quebra a app se Sentry não estiver configurado
"""

import logging

from cloud.config import settings

logger = logging.getLogger(__name__)

_initialized = False


def init_sentry() -> bool:
    """Inicializa Sentry. Retorna True se ativou, False se no-op.

    Idempotente: pode ser chamado várias vezes sem efeito colateral.
    """
    global _initialized

    if _initialized:
        return True

    dsn = settings.sentry_dsn
    if not dsn:
        logger.info("ℹ️  Sentry não configurado (SENTRY_DSN vazio) — no-op")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=settings.ambiente,
            release=f"flowlog-cloud@{settings.versao}",
            traces_sample_rate=0.1,  # 10% das requisições (economiza quota)
            profiles_sample_rate=0.1,
            integrations=[
                FastApiIntegration(),
                StarletteIntegration(),
            ],
            # Filtra health check e OPTIONS (barulho)
            before_send=_filter_events,
        )
        _initialized = True
        logger.info("✅ Sentry inicializado (ambiente=%s)", settings.ambiente)
        return True
    except ImportError:
        logger.warning("⚠️  sentry-sdk não instalado — `pip install sentry-sdk[fastapi]`")
        return False
    except Exception as e:
        logger.error("❌ Falha ao inicializar Sentry: %s", e)
        return False


def _filter_events(event, hint):
    """Filtra eventos barulhentos (health checks, CORS preflight)."""
    request = event.get("request", {})
    url = request.get("url", "")
    if "/v1/health" in url or request.get("method") == "OPTIONS":
        return None
    return event
