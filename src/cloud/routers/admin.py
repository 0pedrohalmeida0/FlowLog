"""Router admin global (v2.1) — super_admin only.

Operações SaaS que atravessam todos os tenants:
    - Dashboard: MRR, churn, inadimplência
    - Lista de tenants (com filtros)
    - Suspender/reativar tenant
    - Promover user a super_admin
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cloud.auth.dependencies import get_current_user, require_super_admin
from cloud.billing.plans import info_plano
from cloud.database import get_session
from cloud.models import Fatura, Plano, StatusFatura, Tenant, User
from cloud.schemas import AdminStats, TenantAdminOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStats)
async def stats(
    admin: Annotated[User, Depends(require_super_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """KPIs globais do SaaS."""
    agora = datetime.now(timezone.utc)
    inicio_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Total de tenants
    r = await session.execute(select(func.count(Tenant.id)))
    total = r.scalar_one()

    # Por plano
    r = await session.execute(
        select(Tenant.plano, func.count(Tenant.id)).group_by(Tenant.plano)
    )
    por_plano = dict(r.all())

    # Em trial (trial_expira_em > agora)
    r = await session.execute(
        select(func.count(Tenant.id)).where(
            Tenant.trial_expira_em.is_not(None),
            Tenant.trial_expira_em > agora,
        )
    )
    em_trial = r.scalar_one()

    tenants_pagos = total - em_trial - por_plano.get(Plano.FREE, 0)
    tenants_free = por_plano.get(Plano.FREE, 0) - em_trial

    # MRR = soma dos preços mensais dos tenants pagos ativos
    mrr = 0
    r = await session.execute(
        select(Tenant.plano).where(Tenant.ativo == True)  # noqa: E712
    )
    for (plano,) in r.all():
        mrr += int(info_plano(plano).preco_mensal_brl * 100)

    # Faturamento do mês (faturas PAGAS)
    r = await session.execute(
        select(func.coalesce(func.sum(Fatura.valor_centavos), 0)).where(
            Fatura.status == StatusFatura.PAGO,
            Fatura.pago_em >= inicio_mes,
        )
    )
    fat_mes = int(r.scalar_one())

    # Inadimplência = pendentes + vencidos
    r = await session.execute(
        select(func.coalesce(func.sum(Fatura.valor_centavos), 0)).where(
            Fatura.status.in_([StatusFatura.PENDENTE.value, StatusFatura.VENCIDO.value])
        )
    )
    inadimplencia = int(r.scalar_one())

    return AdminStats(
        total_tenants=total,
        tenants_pagos=tenants_pagos,
        tenants_free=max(tenants_free, 0),
        tenants_em_trial=em_trial,
        mrr_centavos=mrr,
        faturamento_mes_centavos=fat_mes,
        inadimplencia_centavos=inadimplencia,
    )


@router.get("/tenants", response_model=list[TenantAdminOut])
async def listar_tenants(
    admin: Annotated[User, Depends(require_super_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
    apenas_ativos: bool = True,
    plano: str | None = None,
):
    """Lista todos os tenants (com filtro opcional por plano)."""
    q = select(Tenant).options(selectinload(Tenant.users)).order_by(Tenant.criado_em.desc())
    if apenas_ativos:
        q = q.where(Tenant.ativo == True)  # noqa: E712
    if plano:
        q = q.where(Tenant.plano == plano)
    r = await session.execute(q)
    result = []
    for t in r.scalars():
        result.append(
            TenantAdminOut(
                id=t.id,
                nome=t.nome,
                cnpj=t.cnpj,
                plano=t.plano.value,
                ativo=t.ativo,
                trial_expira_em=t.trial_expira_em,
                criado_em=t.criado_em,
                n_users=len(t.users),
            )
        )
    return result


@router.post("/tenants/{tenant_id}/suspender")
async def suspender_tenant(
    tenant_id: str,
    admin: Annotated[User, Depends(require_super_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
    motivo: str | None = None,
):
    """Suspende (desativa) um tenant. Login passa a ser bloqueado."""
    r = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = r.scalar_one_or_none()
    if t is None:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    t.ativo = False
    await session.commit()
    return {"ok": True, "tenant_id": tenant_id, "motivo": motivo}


@router.post("/tenants/{tenant_id}/reativar")
async def reativar_tenant(
    tenant_id: str,
    admin: Annotated[User, Depends(require_super_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    r = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = r.scalar_one_or_none()
    if t is None:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    t.ativo = True
    await session.commit()
    return {"ok": True, "tenant_id": tenant_id}


@router.post("/users/{user_id}/promover-super-admin")
async def promover_super_admin(
    user_id: str,
    admin: Annotated[User, Depends(require_super_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Promove um user a super_admin (pra expandir o time de operação)."""
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="Você já é super admin")

    r = await session.execute(select(User).where(User.id == user_id))
    u = r.scalar_one_or_none()
    if u is None:
        raise HTTPException(status_code=404, detail="User não encontrado")

    u.super_admin = True
    await session.commit()
    return {"ok": True, "user_id": user_id, "email": u.email}
