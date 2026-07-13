"""Router de dashboard (v2.0 Cloud)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cloud.auth.dependencies import get_current_user
from cloud.database import get_session
from cloud.models import HistoricoMovimentacao, Produto, TipoMovimento, User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/resumo")
async def resumo(
    user: Annotated[User, Depends(get_current_user)],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """KPIs principais do tenant atual."""
    tenant_id = request.state.tenant_id

    # Total de produtos
    r = await session.execute(
        select(func.count(Produto.id), func.coalesce(func.sum(Produto.quantidade), 0))
        .where(Produto.tenant_id == tenant_id)
    )
    total_produtos, total_quantidade = r.one()

    # Produtos em alerta
    r = await session.execute(
        select(func.count(Produto.id)).where(
            Produto.tenant_id == tenant_id,
            Produto.alerta_minimo.is_not(None),
            Produto.quantidade <= Produto.alerta_minimo,
        )
    )
    em_alerta = r.scalar_one()

    # Movimentações do mês
    from datetime import datetime, timezone

    inicio_mes = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    r = await session.execute(
        select(
            func.count(HistoricoMovimentacao.id),
            func.coalesce(func.sum(HistoricoMovimentacao.quantidade), 0),
        ).where(
            HistoricoMovimentacao.tenant_id == tenant_id,
            HistoricoMovimentacao.data_movimentacao >= inicio_mes,
        )
    )
    movs_mes, qtd_movs_mes = r.one()

    return {
        "total_produtos": total_produtos,
        "total_quantidade_estoque": int(total_quantidade),
        "produtos_em_alerta": em_alerta,
        "movimentacoes_mes_atual": movs_mes,
        "quantidade_movimentada_mes": int(qtd_movs_mes),
    }
