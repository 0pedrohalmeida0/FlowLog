"""Google SSO (v2.1 — grátis).

Verifica id_token do Google Sign-In. Não precisa de client_secret
(public client). Setup:
    1. Google Cloud Console → criar OAuth Client ID (Web)
    2. Authorized JavaScript origins: https://app.flowlog.app, http://localhost:5173
    3. Pegar o `client_id` e setar em `GOOGLE_CLIENT_ID`

Fluxo:
    Frontend: `gapi.auth2.getAuthInstance().signIn()` → `id_token`
    POST /v1/auth/google {id_token, tenant_slug?}
    Backend: valida id_token via Google → busca/cria user → retorna JWT

Custo: ZERO. Google não cobra por sign-in.
"""

import logging
from typing import Any

import httpx
from jose import jwt

from cloud.config import settings

logger = logging.getLogger(__name__)

GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


def verificar_id_token(id_token: str) -> dict[str, Any] | None:
    """Valida id_token do Google e retorna claims (email, sub, name, picture).

    Returns None se inválido/expirado/assinatura errada.
    """
    client_id = settings.google_client_id
    if not client_id:
        logger.warning("GOOGLE_CLIENT_ID não configurado — login via Google desabilitado")
        return None

    # 1. Pega certificados do Google (cache 1h em produção)
    try:
        with httpx.Client(timeout=5) as c:
            r = c.get(GOOGLE_CERTS_URL)
            r.raise_for_status()
            certs = r.json()
    except Exception as e:
        logger.error("Falha ao buscar certs do Google: %s", e)
        return None

    # 2. Decodifica header pra saber o kid
    try:
        header = jwt.get_unverified_header(id_token)
        kid = header.get("kid")
        if not kid:
            return None
        key = certs.get(kid)
        if not key:
            return None

        # 3. Valida assinatura, exp, audience
        claims = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=client_id,
        )
    except Exception as e:
        logger.warning("id_token inválido: %s", e)
        return None

    # 4. Validações extras
    if claims.get("email_verified") is not True:
        return None

    return claims
