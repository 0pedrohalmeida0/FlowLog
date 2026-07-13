"""Configurações do FlowLog Cloud (v2.0).

Lê de env vars. Falha no startup se faltar var crítica.
"""

import os
import secrets
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    app_name: str = "FlowLog Cloud"
    versao: str = "2.0.0"
    ambiente: Literal["dev", "staging", "prod"] = "dev"
    debug: bool = False

    # --- Database (PostgreSQL) ---
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "flowlog"
    db_password: str = "flowlog"
    db_name: str = "flowlog"
    db_echo: bool = False  # log SQL

    # --- Auth ---
    jwt_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    jwt_algoritmo: str = "HS256"
    jwt_access_expira_minutos: int = 30
    jwt_refresh_expira_dias: int = 30
    bcrypt_rounds: int = 12

    # --- CORS (frontend) ---
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # --- Billing (v2.0: stub, v2.1: real) ---
    billing_provider: Literal["stub", "stripe", "asaas"] = "stub"
    stripe_api_key: str | None = None
    stripe_webhook_secret: str | None = None
    asaas_api_key: str | None = None

    # --- E-mail (v2.0: stub, v2.1: real) ---
    email_provider: Literal["stub", "smtp", "sendgrid", "resend"] = "stub"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    email_from: str = "FlowLog <noreply@flowlog.app>"

    @property
    def database_url_async(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        """URL sync pra Alembic."""
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
