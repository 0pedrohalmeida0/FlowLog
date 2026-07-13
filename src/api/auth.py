"""Autenticação da API REST (v1.6).

Estratégia:
    - Token simples (Bearer) gerado pelo admin via CLI:
        python -m src.api.cli gerar-token <username>
    - Token é hasheado (bcrypt) e armazenado em `api_tokens` (futuro).
    - Por enquanto: tokens em memória + validação por assinatura.

    Para v1.6.1+: usar JWT com chave secreta do servidor.
"""

import hashlib
import hmac
import os
import secrets

from logging_config import get_logger

logger = get_logger(__name__)

# Chave mestra da API. Em produção, gerar uma vez e guardar no .env
_API_SECRET = os.environ.get("FLOWLOG_API_SECRET", "dev-secret-change-me-in-prod")


def gerar_token(username: str) -> str:
    """Gera um token Bearer pra um usuário (chamado pelo admin).

    Returns:
        Token no formato `fl_<username>_<nonce>_<sig>`. ~50 chars.
        nonce é hex (sem `_`) pra não conflitar com separador.
    """
    nonce = secrets.token_hex(12)  # 24 chars hex, sem underscores
    payload = f"{username}|{nonce}"
    sig = hmac.new(_API_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
    return f"fl_{username}_{nonce}_{sig}"


def validar_token(token: str) -> dict | None:
    """Valida um token Bearer. Retorna dict com {username} se válido.

    Em paralelo, abre uma sessão no module-level `session` pra
    que os services peguem o usuario_id e empresa_id.

    Returns:
        None se token inválido. Dict com username + id se válido.
    """
    if not token.startswith("fl_"):
        return None
    partes = token.split("_")
    if len(partes) != 4:
        return None
    _, username, nonce, sig = partes

    payload = f"{username}|{nonce}"
    sig_esperada = hmac.new(_API_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]

    if not hmac.compare_digest(sig, sig_esperada):
        return None

    # Token válido. Carrega usuário no session.
    # (v1.6.1+: cache de token→user_id pra evitar query em toda request)
    from database import Database
    from session import login as session_login

    db = Database()
    conn = db.connect()
    if not conn:
        return None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, nivel_acesso FROM usuarios WHERE username = %s",
            (username,),
        )
        row = cur.fetchone()
        cur.close()
    finally:
        if conn.is_connected():
            conn.close()

    if not row:
        return None

    session_login(
        usuario_id=row["id"],
        username=username,
        nivel_acesso=row["nivel_acesso"],
        ip="api",  # marcado como api
        user_agent=token[:20] + "...",  # prefixo do token pra rastreamento
    )
    return {"username": username, "id": row["id"]}
