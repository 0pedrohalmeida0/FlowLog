"""Dependencies de auth (v2.0 Cloud)."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cloud.auth.jwt import decodificar_token
from cloud.database import get_session
from cloud.models import User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Decodifica JWT, busca User, anexa tenant_id ao request state.

    Qualquer router que dependa de `current_user` recebe:
        - User (do banco, com tenant_id)
        - request.state.tenant_id (cache pra não precisar pegar do User)
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decodificar_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token sem user_id")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.ativo:
        raise HTTPException(status_code=401, detail="Usuário não encontrado ou inativo")

    # Cache no request pra não precisar pegar do User sempre
    request.state.tenant_id = user.tenant_id
    request.state.user_id = user.id
    request.state.user_email = user.email

    return user


async def get_tenant_id(request: Request) -> str:
    """Pega tenant_id do request state (setado por get_current_user)."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant não identificado")
    return tenant_id


async def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    """Decorator: exige nível ADMIN (3)."""
    from cloud.models import NivelAcesso

    if user.nivel_acesso != NivelAcesso.ADMIN:
        raise HTTPException(status_code=403, detail="Acesso restrito a admins")
    return user
