"""Observability (v2.1 — Sentry free tier).

Por padrão Sentry é no-op (não quebra se SENTRY_DSN não estiver setado).
Quando o Sentry SDK é instalado E SENTRY_DSN configurado, ativa.

Free tier: 5.000 eventos/mês, 1 projeto, 7 dias de retenção.
Suficiente pra MVP com 50-100 tenants ativos.
"""
