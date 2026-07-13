"""Model Fatura (v2.1 — billing manual).

Sem Stripe/ASAAS: o admin gera faturas via PIX/boleto manualmente,
sistema só rastreia status (pendente/pago/cancelado/vencido).

Quando migrar pra Stripe/ASAAS na v2.2, o webhook atualiza o status
diretamente aqui.
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from cloud.database import Base
from cloud.models.base import TenantScopedModel, gen_uuid


class StatusFatura(str, PyEnum):
    PENDENTE = "pendente"
    PAGO = "pago"
    CANCELADO = "cancelado"
    VENCIDO = "vencido"


class MetodoPagamento(str, PyEnum):
    PIX = "pix"
    BOLETO = "boleto"
    TRANSFERENCIA = "transferencia"
    CARTAO = "cartao"  # futuro v2.2 com Stripe


class Fatura(TenantScopedModel):
    __tablename__ = "faturas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)

    # Identificação legível (FlowLog-2026-07-0001)
    numero: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)

    # Valores
    valor_centavos: Mapped[int] = mapped_column(Numeric(12, 0), nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status
    status: Mapped[StatusFatura] = mapped_column(
        Enum(StatusFatura, native_enum=False, length=16),
        default=StatusFatura.PENDENTE,
        nullable=False,
        index=True,
    )
    metodo: Mapped[MetodoPagamento | None] = mapped_column(
        Enum(MetodoPagamento, native_enum=False, length=16), nullable=True
    )

    # Datas
    emitido_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    vence_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pago_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Quem marcou como pago (admin user id)
    marcada_por: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Fatura {self.numero} R${self.valor_centavos/100:.2f} {self.status.value}>"
