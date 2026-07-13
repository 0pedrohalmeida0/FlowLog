"""Router de branding (v2.1 — white-label por tenant).

Cada tenant configura:
    - nome_exibicao: aparece no header (em vez de "FlowLog")
    - logo_url: canto superior esquerdo
    - cores (CSS vars)
    - dominio_custom: pra revenda (CNAME em v2.2)

Endpoint público /v1/branding/public/{tenant_slug} permite que a página
de login já saiba o tema antes do user logar.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cloud.auth.dependencies import get_current_user, require_admin
from cloud.database import get_session
from cloud.models import Branding, Tenant, User
from cloud.schemas import BrandingOut, BrandingPublic, BrandingUpdate

router = APIRouter(prefix="/branding", tags=["branding"])


# ============================================================
# Admin do tenant configura
# ============================================================


@router.get("/me", response_model=BrandingOut)
async def meu_branding(
    user: Annotated[User, Depends(require_admin)],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Retorna branding do tenant atual (cria default se não existe)."""
    tenant_id = request.state.tenant_id
    r = await session.execute(select(Branding).where(Branding.tenant_id == tenant_id))
    branding = r.scalar_one_or_none()

    if branding is None:
        # Cria default
        r = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = r.scalar_one()
        branding = Branding(tenant_id=tenant_id, nome_exibicao=tenant.nome)
        session.add(branding)
        await session.commit()
        await session.refresh(branding)

    return BrandingOut.model_validate(branding)


@router.patch("/me", response_model=BrandingOut)
async def atualizar_branding(
    body: BrandingUpdate,
    user: Annotated[User, Depends(require_admin)],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Atualiza branding do tenant atual."""
    tenant_id = request.state.tenant_id
    r = await session.execute(select(Branding).where(Branding.tenant_id == tenant_id))
    branding = r.scalar_one_or_none()

    if branding is None:
        branding = Branding(tenant_id=tenant_id)
        session.add(branding)

    updates = body.model_dump(exclude_none=True)
    for k, v in updates.items():
        setattr(branding, k, v)

    await session.commit()
    await session.refresh(branding)
    return BrandingOut.model_validate(branding)


# ============================================================
# Público: usado pela página de login pra saber o tema
# ============================================================


@router.get("/public/{tenant_slug}", response_model=BrandingPublic)
async def branding_publico(
    tenant_slug: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Branding público (sem auth). `tenant_slug` é o CNPJ ou nome normalizado."""
    # Tenta por CNPJ
    cnpj_limpo = tenant_slug.replace(".", "").replace("/", "").replace("-", "")
    r = await session.execute(
        select(Tenant).where(
            (Tenant.cnpj == cnpj_limpo) | (Tenant.id == tenant_slug)
        )
    )
    tenant = r.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")

    r = await session.execute(select(Branding).where(Branding.tenant_id == tenant.id))
    branding = r.scalar_one_or_none()

    if branding is None:
        # Retorna default sem persistir
        return BrandingPublic(
            nome_exibicao=tenant.nome,
            cor_primaria="#1f6feb",
            cor_fundo="#f9fafb",
            cor_texto="#111827",
            logo_url=None,
            css_vars={
                "--flowlog-primary": "#1f6feb",
                "--flowlog-bg": "#f9fafb",
                "--flowlog-text": "#111827",
            },
        )

    return BrandingPublic(
        nome_exibicao=branding.nome_exibicao or tenant.nome,
        cor_primaria=branding.cor_primaria,
        cor_fundo=branding.cor_fundo,
        cor_texto=branding.cor_texto,
        logo_url=branding.logo_url,
        css_vars=branding.to_css_vars(),
    )
