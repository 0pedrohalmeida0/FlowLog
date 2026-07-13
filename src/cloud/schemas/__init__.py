"""Schemas Pydantic do Cloud (v2.0)."""

from cloud.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MovimentacaoIn,
    MovimentacaoOut,
    ProdutoCreate,
    ProdutoEdit,
    ProdutoOut,
    RefreshRequest,
    RefreshResponse,
    SignupRequest,
    SignupResponse,
    TenantOut,
    TenantUpdate,
)

__all__ = [
    "LoginRequest",
    "LoginResponse",
    "MovimentacaoIn",
    "MovimentacaoOut",
    "ProdutoCreate",
    "ProdutoEdit",
    "ProdutoOut",
    "RefreshRequest",
    "RefreshResponse",
    "SignupRequest",
    "SignupResponse",
    "TenantOut",
    "TenantUpdate",
]
