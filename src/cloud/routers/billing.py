"""Router de billing (v2.1 — manual).

Sem Stripe/ASAAS: admin cria faturas via PIX/boleto/transferência.
Cliente vê faturas pendentes no dashboard. Admin marca como pago.

Como migrar pra Stripe na v2.2:
    1. Webhook do Stripe chama POST /v1/billing/webhook
    2. Webhook atualiza status da fatura (id=metadata.flowlog_fatura_id)
    3. API do Stripe é chamada SÓ pra gerar link de pagamento (não pra "existir")
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cloud.auth.dependencies import (
    get_current_user,
    get_tenant_id,
    require_super_admin,
)
from cloud.database import get_session
from cloud.models import Fatura, MetodoPagamento, StatusFatura, User
from cloud.schemas import FaturaCreate, FaturaMarcarPago, FaturaOut

router = APIRouter(prefix="/billing", tags=["billing"])


def _gerar_numero() -> str:
    """FlowLog-YYYYMM-NNNN. Útil pra invoice/boleto."""
    agora = datetime.now(timezone.utc)
    return f"FlowLog-{agora:%Y%m}-XXXX"  # número completo é gerado no service


@router.get("/minhas", response_model=list[FaturaOut])
async def listar_minhas(
    user: Annotated[User, Depends(get_current_user)],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Lista faturas do tenant do user logado."""
    tenant_id = request.state.tenant_id
    result = await session.execute(
        select(Fatura)
        .where(Fatura.tenant_id == tenant_id)
        .order_by(Fatura.emitido_em.desc())
    )
    return [FaturaOut.model_validate(f) for f in result.scalars()]


@router.get("/minhas/pendentes", response_model=list[FaturaOut])
async def listar_pendentes(
    user: Annotated[User, Depends(get_current_user)],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Só faturas pendentes/vencidas (banner no dashboard)."""
    tenant_id = request.state.tenant_id
    result = await session.execute(
        select(Fatura)
        .where(
            Fatura.tenant_id == tenant_id,
            Fatura.status.in_([StatusFatura.PENDENTE.value, StatusFatura.VENCIDO.value]),
        )
        .order_by(Fatura.vence_em.asc())
    )
    return [FaturaOut.model_validate(f) for f in result.scalars()]


# ============================================================
# Endpoints super_admin
# ============================================================


@router.get("/admin/todas", response_model=list[FaturaOut])
async def admin_listar_todas(
    admin: Annotated[User, Depends(require_super_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
    status_filter: str | None = None,
):
    """Lista TODAS as faturas (super admin)."""
    q = select(Fatura).order_by(Fatura.emitido_em.desc()).limit(500)
    if status_filter:
        q = q.where(Fatura.status == status_filter)
    result = await session.execute(q)
    return [FaturaOut.model_validate(f) for f in result.scalars()]


@router.post("/admin/criar", response_model=FaturaOut, status_code=201)
async def admin_criar_fatura(
    body: FaturaCreate,
    admin: Annotated[User, Depends(require_super_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Cria fatura pra um tenant. Gera número sequencial."""
    # Conta faturas do mês pra numeração
    from datetime import datetime, timezone

    agora = datetime.now(timezone.utc)
    inicio_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    r = await session.execute(
        select(Fatura).where(Fatura.emitido_em >= inicio_mes)
    )
    n_existente = len(r.scalars().all())
    numero = f"FlowLog-{agora:%Y%m}-{n_existente + 1:04d}"

    fatura = Fatura(
        tenant_id=body.tenant_id,
        numero=numero,
        valor_centavos=body.valor_centavos,
        descricao=body.descricao,
        metodo=MetodoPagamento(body.metodo),
        status=StatusFatura.PENDENTE,
        vence_em=body.vence_em,
        observacao=body.observacao,
    )
    session.add(fatura)
    await session.commit()
    await session.refresh(fatura)
    return FaturaOut.model_validate(fatura)


@router.post("/admin/{fatura_id}/marcar-pago", response_model=FaturaOut)
async def admin_marcar_pago(
    fatura_id: str,
    body: FaturaMarcarPago,
    admin: Annotated[User, Depends(require_super_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Admin marcou que recebeu o pagamento (PIX caiu, boleto compensou)."""
    from datetime import datetime, timezone

    result = await session.execute(select(Fatura).where(Fatura.id == fatura_id))
    fatura = result.scalar_one_or_none()
    if fatura is None:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    if fatura.status == StatusFatura.PAGO:
        raise HTTPException(status_code=409, detail="Fatura já está paga")

    fatura.status = StatusFatura.PAGO
    fatura.metodo = MetodoPagamento(body.metodo)
    fatura.pago_em = datetime.now(timezone.utc)
    fatura.marcada_por = admin.id
    if body.observacao:
        fatura.observacao = (fatura.observacao or "") + f"\n[admin {admin.email}] {body.observacao}"

    await session.commit()
    await session.refresh(fatura)

    # TODO v2.1.1: enviar email de "fatura paga" via cloud.email.service
    return FaturaOut.model_validate(fatura)


@router.post("/admin/{fatura_id}/cancelar", response_model=FaturaOut)
async def admin_cancelar(
    fatura_id: str,
    admin: Annotated[User, Depends(require_super_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
    motivo: str | None = None,
):
    result = await session.execute(select(Fatura).where(Fatura.id == fatura_id))
    fatura = result.scalar_one_or_none()
    if fatura is None:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    if fatura.status == StatusFatura.PAGO:
        raise HTTPException(status_code=409, detail="Fatura já foi paga, não pode cancelar")

    fatura.status = StatusFatura.CANCELADO
    if motivo:
        fatura.observacao = (fatura.observacao or "") + f"\n[admin {admin.email}] CANCELADA: {motivo}"
    await session.commit()
    await session.refresh(fatura)
    return FaturaOut.model_validate(fatura)
