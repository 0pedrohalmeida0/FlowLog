"""Auth do Cloud (v2.0)."""

from cloud.auth.dependencies import get_current_user, get_tenant_id, require_admin
from cloud.auth.jwt import criar_access_token, criar_refresh_token, decodificar_token
from cloud.auth.password import hash_password, verify_password

__all__ = [
    "criar_access_token",
    "criar_refresh_token",
    "decodificar_token",
    "get_current_user",
    "get_tenant_id",
    "hash_password",
    "require_admin",
    "verify_password",
]
