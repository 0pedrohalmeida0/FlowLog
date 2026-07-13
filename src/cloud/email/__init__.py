"""E-mail (v2.1 — self-hosted via Mailpit por padrão).

Provedores suportados:
    - `stub` (default dev): loga no console, sem envio real
    - `smtp`: SMTP genérico (Mailpit local, Postfix, Gmail, etc)
    - `sendgrid` / `resend`: provedores SaaS (v2.2+ se quiser)

Para dev, Mailpit roda no Docker (porta 1025 SMTP, 8025 web UI).
Em prod, troque `EMAIL_PROVIDER=smtp` + `SMTP_HOST=<seu SMTP>`.
"""

from cloud.email.service import (
    enviar_email,
    email_boas_vindas,
    email_trial_expira,
    email_fatura_gerada,
    email_fatura_paga,
)

__all__ = [
    "email_boas_vindas",
    "email_fatura_gerada",
    "email_fatura_paga",
    "enviar_email",
    "email_trial_expira",
]
