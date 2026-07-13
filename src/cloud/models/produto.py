"""Model Produto (v2.0 Cloud)."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from cloud.database import Base
from cloud.models.base import TenantScopedModel, TimestampModel, gen_uuid


class Produto(TenantScopedModel, TimestampModel):
    __tablename__ = "produtos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    preco_custo: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    preco_venda: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    fornecedor_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("fornecedores.id", ondelete="SET NULL"), nullable=True
    )
    alerta_minimo: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_entrada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint("quantidade >= 0", name="chk_quantidade"),
        CheckConstraint("preco_custo >= 0", name="chk_preco"),
        CheckConstraint("alerta_minimo IS NULL OR alerta_minimo >= 0", name="chk_alerta"),
    )

    def __repr__(self) -> str:
        return f"<Produto {self.nome} qty={self.quantidade}>"
