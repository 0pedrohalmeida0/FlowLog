"""Pydantic schemas do Cloud (v2.0)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# ============================================================
# Auth
# ============================================================


class SignupRequest(BaseModel):
    """Cadastro de novo tenant (empresa) + primeiro user (admin)."""

    tenant_nome: str = Field(..., min_length=2, max_length=255, description="Nome da empresa")
    tenant_cnpj: str | None = Field(None, min_length=14, max_length=18)
    admin_email: EmailStr
    admin_username: str = Field(..., min_length=3, max_length=64)
    admin_senha: str = Field(..., min_length=8, max_length=128)
    plano: Literal["free", "pro", "business"] = "free"


class SignupResponse(BaseModel):
    tenant_id: str
    user_id: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    tenant_id: str
    email: str
    nivel_acesso: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ============================================================
# Produto
# ============================================================


class ProdutoCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    quantidade: int = Field(0, ge=0)
    preco_custo: float = Field(0.0, ge=0)
    preco_venda: float | None = Field(None, ge=0)
    fornecedor_id: str | None = None
    alerta_minimo: int | None = Field(None, ge=0)


class ProdutoOut(BaseModel):
    id: str
    nome: str
    quantidade: int
    preco_custo: float
    preco_venda: float | None
    fornecedor_id: str | None
    alerta_minimo: int | None
    data_entrada: datetime
    criado_em: datetime
    atualizado_em: datetime

    model_config = {"from_attributes": True}


class ProdutoEdit(BaseModel):
    nome: str | None = None
    preco_custo: float | None = None
    preco_venda: float | None = None
    alerta_minimo: int | None = None


class MovimentacaoIn(BaseModel):
    quantidade: int = Field(..., gt=0)


class MovimentacaoOut(BaseModel):
    produto_id: str
    nome: str
    qtd_anterior: int
    qtd_nova: int


# ============================================================
# Tenant
# ============================================================


class TenantOut(BaseModel):
    id: str
    nome: str
    cnpj: str | None
    plano: str
    ativo: bool
    criado_em: datetime

    model_config = {"from_attributes": True}


class TenantUpdate(BaseModel):
    nome: str | None = None
    cnpj: str | None = None
    plano: Literal["free", "pro", "business"] | None = None
