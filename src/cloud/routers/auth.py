"""Router de auth (v2.0 Cloud)."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cloud.auth import (
    criar_access_token,
    criar_refresh_token,
    decodificar_token,
    get_current_user,
    hash_password,
    verify_password,
)
from cloud.database import get_session
from cloud.models import NivelAcesso, Plano, Tenant, User
from cloud.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    SignupRequest,
    SignupResponse,
    TenantOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    body: SignupRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Cria novo tenant + primeiro user admin.

    Onboarding self-service: 14 dias trial, plano Free default.
    """
    # Verifica email duplicado
    result = await session.execute(select(User).where(User.email == body.admin_email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email já cadastrado")

    # Cria tenant
    tenant = Tenant(
        nome=body.tenant_nome,
        cnpj=body.tenant_cnpj,
        plano=Plano(body.plano),
        trial_expira_em=datetime.now(timezone.utc) + timedelta(days=14),
        ativo=True,
    )
    session.add(tenant)
    await session.flush()  # pra pegar o id

    # Cria user admin
    user = User(
        tenant_id=tenant.id,
        email=body.admin_email,
        username=body.admin_username,
        senha_hash=hash_password(body.admin_senha),
        nivel_acesso=NivelAcesso.ADMIN,
        ativo=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return SignupResponse(
        tenant_id=tenant.id,
        user_id=user.id,
        access_token=criar_access_token(user.id, tenant.id, user.email),
        refresh_token=criar_refresh_token(user.id),
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Autentica user e retorna tokens."""
    result = await session.execute(
        select(User)
        .where(User.email == body.email)
        .options(selectinload(User.tenant))
    )
    user = result.scalar_one_or_none()

    if user is None or not user.ativo or not verify_password(body.senha, user.senha_hash):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    if not user.tenant.ativo:
        raise HTTPException(status_code=403, detail="Tenant desativado. Contate o suporte.")

    return LoginResponse(
        access_token=criar_access_token(user.id, user.tenant_id, user.email),
        refresh_token=criar_refresh_token(user.id),
        user_id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        nivel_acesso=user.nivel_acesso.value,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    body: RefreshRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Troca refresh token por novo access token."""
    payload = decodificar_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    user_id = payload.get("sub")
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.ativo:
        raise HTTPException(status_code=401, detail="User inválido")

    return RefreshResponse(
        access_token=criar_access_token(user.id, user.tenant_id, user.email),
    )


@router.get("/me", response_model=TenantOut)
async def me(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Retorna dados do tenant atual."""
    result = await session.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = result.scalar_one()
    return TenantOut.model_validate(tenant)
