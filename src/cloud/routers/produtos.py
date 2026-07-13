"""Router de produtos (v2.0 Cloud)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cloud.auth.dependencies import get_current_user
from cloud.database import get_session
from cloud.models import HistoricoMovimentacao, Produto, TipoMovimento, User
from cloud.schemas import (
    MovimentacaoIn,
    MovimentacaoOut,
    ProdutoCreate,
    ProdutoEdit,
    ProdutoOut,
)

router = APIRouter(prefix="/produtos", tags=["produtos"])


@router.get("", response_model=list[ProdutoOut])
async def listar(
    user: Annotated[User, Depends(get_current_user)],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Lista produtos do tenant atual (filtro multi-tenant automático)."""
    tenant_id = request.state.tenant_id
    result = await session.execute(
        select(Produto).where(Produto.tenant_id == tenant_id).order_by(Produto.nome)
    )
    return [ProdutoOut.model_validate(p) for p in result.scalars()]


@router.post("", response_model=ProdutoOut, status_code=status.HTTP_201_CREATED)
async def criar(
    body: ProdutoCreate,
    user: Annotated[User, Depends(get_current_user)],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Cadastra um produto no tenant atual."""
    tenant_id = request.state.tenant_id
    prod = Produto(
        tenant_id=tenant_id,
        nome=body.nome,
        quantidade=body.quantidade,
        preco_custo=body.preco_custo,
        preco_venda=body.preco_venda,
        fornecedor_id=body.fornecedor_id,
        alerta_minimo=body.alerta_minimo,
    )
    session.add(prod)
    await session.commit()
    await session.refresh(prod)
    return ProdutoOut.model_validate(prod)


@router.get("/{produto_id}", response_model=ProdutoOut)
async def buscar(
    produto_id: str,
    user: Annotated[User, Depends(get_current_user)],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    tenant_id = request.state.tenant_id
    result = await session.execute(
        select(Produto).where(
            Produto.id == produto_id, Produto.tenant_id == tenant_id
        )
    )
    prod = result.scalar_one_or_none()
    if prod is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return ProdutoOut.model_validate(prod)


@router.patch("/{produto_id}", response_model=ProdutoOut)
async def editar(
    produto_id: str,
    body: ProdutoEdit,
    user: Annotated[User, Depends(get_current_user)],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    tenant_id = request.state.tenant_id
    result = await session.execute(
        select(Produto).where(
            Produto.id == produto_id, Produto.tenant_id == tenant_id
        )
    )
    prod = result.scalar_one_or_none()
    if prod is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    # Aplica só os campos enviados
    updates = body.model_dump(exclude_none=True)
    for k, v in updates.items():
        setattr(prod, k, v)
    await session.commit()
    await session.refresh(prod)
    return ProdutoOut.model_validate(prod)


@router.post("/{produto_id}/entrada", response_model=MovimentacaoOut)
async def entrada(
    produto_id: str,
    body: MovimentacaoIn,
    user: Annotated[User, Depends(get_current_user)],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Registra entrada de estoque."""
    tenant_id = request.state.tenant_id
    result = await session.execute(
        select(Produto).where(
            Produto.id == produto_id, Produto.tenant_id == tenant_id
        ).with_for_update()  # SELECT FOR UPDATE
    )
    prod = result.scalar_one_or_none()
    if prod is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    qtd_anterior = prod.quantidade
    prod.quantidade += body.quantidade

    # Registra histórico
    mov = HistoricoMovimentacao(
        tenant_id=tenant_id,
        produto_id=prod.id,
        tipo=TipoMovimento.ENTRADA,
        quantidade=body.quantidade,
        usuario_id=user.id,
    )
    session.add(mov)
    await session.commit()
    await session.refresh(prod)

    return MovimentacaoOut(
        produto_id=prod.id,
        nome=prod.nome,
        qtd_anterior=qtd_anterior,
        qtd_nova=prod.quantidade,
    )


@router.post("/{produto_id}/saida", response_model=MovimentacaoOut)
async def saida(
    produto_id: str,
    body: MovimentacaoIn,
    user: Annotated[User, Depends(get_current_user)],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Registra saída de estoque."""
    tenant_id = request.state.tenant_id
    result = await session.execute(
        select(Produto).where(
            Produto.id == produto_id, Produto.tenant_id == tenant_id
        ).with_for_update()
    )
    prod = result.scalar_one_or_none()
    if prod is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    if prod.quantidade < body.quantidade:
        raise HTTPException(
            status_code=409,
            detail=f"Estoque insuficiente (saldo: {prod.quantidade})",
        )

    qtd_anterior = prod.quantidade
    prod.quantidade -= body.quantidade

    mov = HistoricoMovimentacao(
        tenant_id=tenant_id,
        produto_id=prod.id,
        tipo=TipoMovimento.SAIDA,
        quantidade=body.quantidade,
        usuario_id=user.id,
    )
    session.add(mov)
    await session.commit()
    await session.refresh(prod)

    return MovimentacaoOut(
        produto_id=prod.id,
        nome=prod.nome,
        qtd_anterior=qtd_anterior,
        qtd_nova=prod.quantidade,
    )
