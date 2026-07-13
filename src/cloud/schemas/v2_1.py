"""Schemas da v2.1: billing manual, white-label, admin global."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, HttpUrl


# ============================================================
# Fatura (billing manual)
# ============================================================


class FaturaCreate(BaseModel):
    """Admin cria fatura pra um tenant."""

    tenant_id: str
    valor_centavos: int = Field(..., ge=1, le=10_000_000_00, description="Em centavos (R$ 99,00 = 9900)")
    descricao: str = Field(..., min_length=3, max_length=255)
    metodo: Literal["pix", "boleto", "transferencia", "cartao"] = "pix"
    vence_em: datetime
    observacao: str | None = None


class FaturaOut(BaseModel):
    id: str
    numero: str
    tenant_id: str
    valor_centavos: int
    descricao: str
    status: str
    metodo: str | None
    emitido_em: datetime
    vence_em: datetime
    pago_em: datetime | None
    observacao: str | None

    model_config = {"from_attributes": True}


class FaturaMarcarPago(BaseModel):
    """Admin marca fatura como paga (após receber PIX/boleto)."""

    metodo: Literal["pix", "boleto", "transferencia", "cartao"]
    observacao: str | None = None


# ============================================================
# Branding (white-label)
# ============================================================


class BrandingUpdate(BaseModel):
    nome_exibicao: str | None = Field(None, max_length=64)
    logo_url: str | None = Field(None, max_length=512)
    cor_primaria: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    cor_fundo: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    cor_texto: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    dominio_custom: str | None = Field(None, max_length=255)


class BrandingOut(BaseModel):
    tenant_id: str
    nome_exibicao: str | None
    logo_url: str | None
    cor_primaria: str
    cor_fundo: str
    cor_texto: str
    dominio_custom: str | None

    model_config = {"from_attributes": True}


class BrandingPublic(BaseModel):
    """Retornado sem auth (pra página de login saber que tema aplicar)."""

    nome_exibicao: str | None
    cor_primaria: str
    cor_fundo: str
    cor_texto: str
    logo_url: str | None
    css_vars: dict[str, str]


# ============================================================
# Admin
# ============================================================


class AdminStats(BaseModel):
    """MRR, total de tenants ativos, churn simples."""

    total_tenants: int
    tenants_pagos: int
    tenants_free: int
    tenants_em_trial: int
    mrr_centavos: int  # Monthly Recurring Revenue
    faturamento_mes_centavos: int  # Total faturado (pago) no mês
    inadimplencia_centavos: int  # Faturas vencidas + pendentes


class TenantAdminOut(BaseModel):
    id: str
    nome: str
    cnpj: str | None
    plano: str
    ativo: bool
    trial_expira_em: datetime | None
    criado_em: datetime
    n_users: int

    model_config = {"from_attributes": True}


# ============================================================
# Google SSO
# ============================================================


class GoogleLoginRequest(BaseModel):
    """Frontend envia o id_token que recebeu do Google Sign-In."""

    id_token: str = Field(..., min_length=10)
    tenant_slug: str | None = Field(
        None,
        description=(
            "Slug do tenant pra onde logar. Se None e email já existe, loga no tenant do user. "
            "Se email novo, retorna erro pedindo signup."
        ),
    )


class GoogleSignupRequest(BaseModel):
    """Cria novo tenant via Google."""

    id_token: str
    tenant_nome: str = Field(..., min_length=2, max_length=255)
    plano: Literal["free", "pro", "business"] = "free"
