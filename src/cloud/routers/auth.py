"""Router de auth (v2.1 Cloud)."""

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
from cloud.auth.google import verificar_id_token
from cloud.database import get_session
from cloud.email import email_boas_vindas
from cloud.models import Branding, NivelAcesso, Plano, Tenant, User
from cloud.schemas import (
    GoogleLoginRequest,
    GoogleSignupRequest,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    SignupRequest,
    SignupResponse,
    TenantOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================
# Signup / Login clássicos
# ============================================================


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
    result = await session.execute(select(User).where(User.email == body.admin_email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email já cadastrado")

    trial_expira = datetime.now(timezone.utc) + timedelta(days=14)
    tenant = Tenant(
        nome=body.tenant_nome,
        cnpj=body.tenant_cnpj,
        plano=Plano(body.plano),
        trial_expira_em=trial_expira,
        ativo=True,
    )
    session.add(tenant)
    await session.flush()

    user = User(
        tenant_id=tenant.id,
        email=body.admin_email,
        username=body.admin_username,
        senha_hash=hash_password(body.admin_senha),
        nivel_acesso=NivelAcesso.ADMIN,
        ativo=True,
    )
    session.add(user)

    # Branding default pro tenant
    branding = Branding(tenant_id=tenant.id, nome_exibicao=tenant.nome)
    session.add(branding)

    await session.commit()
    await session.refresh(user)

    # E-mail de boas-vindas (não bloqueante se falhar)
    try:
        email_boas_vindas(
            tenant_nome=tenant.nome,
            admin_email=user.email,
            trial_expira_em=trial_expira.strftime("%d/%m/%Y"),
        )
    except Exception:
        pass

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
    result = await session.execute(
        select(User)
        .where(User.email == body.email)
        .options(selectinload(User.tenant))
    )
    user = result.scalar_one_or_none()

    if user is None or not user.ativo or not user.senha_hash or not verify_password(body.senha, user.senha_hash):
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
    result = await session.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = result.scalar_one()
    return TenantOut.model_validate(tenant)


# ============================================================
# Google SSO (v2.1)
# ============================================================


@router.post("/google/login", response_model=LoginResponse)
async def google_login(
    body: GoogleLoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Login via Google Sign-In (id_token verificado contra Google).

    Se email já existe: loga normalmente.
    Se email novo: 404 (orienta a fazer signup).
    """
    claims = verificar_id_token(body.id_token)
    if claims is None:
        raise HTTPException(status_code=401, detail="Token Google inválido")

    email = claims.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Google não retornou email")

    result = await session.execute(
        select(User).where(User.email == email).options(selectinload(User.tenant))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Email não cadastrado. Faça signup primeiro.",
        )
    if not user.ativo:
        raise HTTPException(status_code=403, detail="Usuário desativado")
    if not user.tenant.ativo:
        raise HTTPException(status_code=403, detail="Tenant desativado")

    # Atualiza google_id e avatar se primeira vez
    if not user.google_id:
        user.google_id = claims.get("sub")
        user.avatar_url = claims.get("picture")
        await session.commit()

    return LoginResponse(
        access_token=criar_access_token(user.id, user.tenant_id, user.email),
        refresh_token=criar_refresh_token(user.id),
        user_id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        nivel_acesso=user.nivel_acesso.value,
    )


@router.post("/google/signup", response_model=SignupResponse, status_code=201)
async def google_signup(
    body: GoogleSignupRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Signup via Google (cria tenant + admin numa chamada só)."""
    claims = verificar_id_token(body.id_token)
    if claims is None:
        raise HTTPException(status_code=401, detail="Token Google inválido")

    email = claims.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Google não retornou email")

    # Verifica se email já existe
    result = await session.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email já cadastrado (use /google/login)")

    trial_expira = datetime.now(timezone.utc) + timedelta(days=14)
    tenant = Tenant(
        nome=body.tenant_nome,
        plano=Plano(body.plano),
        trial_expira_em=trial_expira,
        ativo=True,
    )
    session.add(tenant)
    await session.flush()

    user = User(
        tenant_id=tenant.id,
        email=email,
        username=email.split("@")[0][:64],
        senha_hash=None,  # sem senha — só Google
        google_id=claims.get("sub"),
        avatar_url=claims.get("picture"),
        nivel_acesso=NivelAcesso.ADMIN,
        ativo=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    try:
        email_boas_vindas(
            tenant_nome=tenant.nome,
            admin_email=user.email,
            trial_expira_em=trial_expira.strftime("%d/%m/%Y"),
        )
    except Exception:
        pass

    return SignupResponse(
        tenant_id=tenant.id,
        user_id=user.id,
        access_token=criar_access_token(user.id, tenant.id, user.email),
        refresh_token=criar_refresh_token(user.id),
    )
