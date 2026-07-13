"""Helpers de senha (bcrypt) — v2.0 Cloud."""

import bcrypt

from cloud.config import settings


def hash_password(senha: str) -> str:
    """Hash bcrypt. Limita 72 bytes (CR-03 do v1.4 já tratado com SHA-256)."""
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt(rounds=settings.bcrypt_rounds)).decode("utf-8")


def verify_password(senha_plana: str, senha_hash: str) -> bool:
    """Verifica senha contra hash."""
    if not senha_plana or not senha_hash:
        return False
    try:
        return bcrypt.checkpw(senha_plana.encode("utf-8"), senha_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False
