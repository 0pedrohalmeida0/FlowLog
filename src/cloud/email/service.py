"""Serviço de envio de e-mail (v2.1).

Por padrão usa stub (loga no console). Em dev, configurar SMTP pra Mailpit
(email fica visível em http://localhost:8025). Em prod, SMTP genérico.

Vantagens:
    - Zero custo (Mailpit é self-hosted)
    - Funciona offline (sem API key de SaaS)
    - Templates em PT-BR já prontos

Pra trocar pra Resend/SendGrid na v2.2, basta implementar o bloco do
provider correspondente em `_enviar()`.
"""

import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Any

from cloud.config import settings
from cloud.email.templates import (
    template_boas_vindas,
    template_fatura_gerada,
    template_fatura_paga,
    template_trial_expira,
)

logger = logging.getLogger(__name__)


# ============================================================
# Envio core
# ============================================================


def _enviar(
    to: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> dict[str, Any]:
    """Envia e-mail via provider configurado.

    Returns: dict com status (e.g. {"provider": "smtp", "to": ..., "ok": True})
    """
    provider = settings.email_provider

    if provider == "stub":
        # Dev: só loga
        logger.info(
            "📧 [STUB EMAIL] To: %s | Subject: %s\n%s\n---",
            to,
            subject,
            text_body or html_body[:200],
        )
        return {"provider": "stub", "to": to, "subject": subject, "ok": True}

    if provider == "smtp":
        if not settings.smtp_host:
            logger.warning("SMTP_HOST não configurado — caindo pra stub")
            return _enviar(to, subject, html_body, text_body)  # re-fallback

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.email_from
        msg["To"] = to
        if text_body:
            msg.set_content(text_body)
        else:
            msg.set_content("Versão HTML requerida — visualize no cliente de e-mail.")
        msg.add_alternative(html_body, subtype="html")

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as s:
                s.starttls()
                if settings.smtp_user and settings.smtp_password:
                    s.login(settings.smtp_user, settings.smtp_password)
                s.send_message(msg)
            logger.info("📧 [SMTP] enviado: %s → %s", subject, to)
            return {"provider": "smtp", "to": to, "subject": subject, "ok": True}
        except Exception as e:
            logger.error("❌ [SMTP] falhou: %s", e)
            return {"provider": "smtp", "to": to, "ok": False, "error": str(e)}

    raise ValueError(f"Provider de e-mail não suportado: {provider}")


# ============================================================
# Helpers semânticos
# ============================================================


def enviar_email(
    to: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> dict[str, Any]:
    """API pública. Tenta enviar; se falhar, loga mas NÃO quebra (não-bloqueante)."""
    try:
        return _enviar(to, subject, html_body, text_body)
    except Exception as e:
        logger.error("❌ Erro enviando e-mail: %s", e)
        return {"ok": False, "error": str(e)}


def email_boas_vindas(tenant_nome: str, admin_email: str, trial_expira_em: str) -> dict:
    return enviar_email(
        to=admin_email,
        subject=f"🌊 Bem-vindo ao FlowLog, {tenant_nome}!",
        html_body=template_boas_vindas(tenant_nome, admin_email, trial_expira_em),
        text_body=f"Olá {tenant_nome}! Bem-vindo ao FlowLog. Trial até {trial_expira_em}.",
    )


def email_trial_expira(tenant_nome: str, admin_email: str, dias_restantes: int) -> dict:
    return enviar_email(
        to=admin_email,
        subject=f"⏰ Seu trial expira em {dias_restantes} dia(s)",
        html_body=template_trial_expira(tenant_nome, dias_restantes),
        text_body=f"Seu trial expira em {dias_restantes} dia(s). Escolha um plano: https://app.flowlog.app/billing",
    )


def email_fatura_gerada(
    tenant_nome: str,
    admin_email: str,
    numero: str,
    valor_centavos: int,
    metodo: str,
    vencimento: str,
    pix_chave: str | None = None,
) -> dict:
    return enviar_email(
        to=admin_email,
        subject=f"💰 Nova fatura: {numero}",
        html_body=template_fatura_gerada(
            tenant_nome, numero, valor_centavos / 100, metodo, vencimento, pix_chave
        ),
        text_body=f"Fatura {numero} no valor de R$ {valor_centavos/100:.2f}. Vencimento: {vencimento}.",
    )


def email_fatura_paga(tenant_nome: str, admin_email: str, numero: str, valor_centavos: int) -> dict:
    return enviar_email(
        to=admin_email,
        subject=f"✅ Pagamento confirmado: {numero}",
        html_body=template_fatura_paga(tenant_nome, numero, valor_centavos / 100),
        text_body=f"Pagamento da fatura {numero} (R$ {valor_centavos/100:.2f}) confirmado.",
    )
