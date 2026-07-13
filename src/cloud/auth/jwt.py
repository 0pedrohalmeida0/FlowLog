"""JWT helpers (v2.0 Cloud)."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from cloud.config import settings


def criar_access_token(
    user_id: str,
    tenant_id: str,
    email: str,
    extra: dict[str, Any] | None = None,
) -> str:
    """Gera um access token (curta duração: 30 min default)."""
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "email": email,
        "type": "access",
        "iat": agora,
        "exp": agora + timedelta(minutes=settings.jwt_access_expira_minutos),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algoritmo)


def criar_refresh_token(user_id: str) -> str:
    """Gera um refresh token (longa duração: 30 dias default)."""
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": agora,
        "exp": agora + timedelta(days=settings.jwt_refresh_expira_dias),
        "jti": __import__("secrets").token_urlsafe(16),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algoritmo)


def decodificar_token(token: str) -> dict | None:
    """Decodifica e valida um JWT. None se inválido ou expirado."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algoritmo])
    except JWTError:
        return None
