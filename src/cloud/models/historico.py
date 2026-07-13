"""Model HistoricoMovimentacao (v2.0 Cloud)."""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from cloud.database import Base
from cloud.models.base import TenantScopedModel, gen_uuid


class TipoMovimento(str, PyEnum):
    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"


class HistoricoMovimentacao(TenantScopedModel):
    __tablename__ = "historico_movimentacoes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    produto_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("produtos.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    tipo: Mapped[TipoMovimento] = mapped_column(
        Enum(TipoMovimento, native_enum=False, length=16), nullable=False
    )
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    data_movimentacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    usuario_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        CheckConstraint("quantidade > 0", name="chk_qtd_hist"),
    )
