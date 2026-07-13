"""Model Tenant (v2.0 Cloud).

Tenant = conta de cliente. Pode ter múltiplos usuários.
Multi-tenant real: cada row de negócio tem `tenant_id` apontando aqui.
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, String, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from cloud.database import Base
from cloud.models.base import gen_uuid


class Plano(str, PyEnum):
    """Planos de assinatura do Cloud (v2.0)."""

    FREE = "free"           # 1 user, 100 produtos
    PRO = "pro"             # 5 users, ilimitado
    BUSINESS = "business"   # 50 users, integrações


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    cnpj: Mapped[str | None] = mapped_column(String(14), nullable=True, index=True)

    # Plano e billing
    plano: Mapped[Plano] = mapped_column(
        Enum(Plano, native_enum=False, length=16),
        default=Plano.FREE,
        nullable=False,
    )
    trial_expira_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Metadata
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Tenant {self.id} {self.nome} ({self.plano.value})>"
