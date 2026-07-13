"""Model base com `tenant_id` (multi-tenant row-level)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from cloud.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class TenantScopedModel(Base):
    """Mixin: adiciona `tenant_id` em toda tabela de negócio.

    Toda query de produto, fornecedor, etc. DEVE filtrar por tenant_id.
    O TenantFilter middleware faz isso automaticamente.
    """

    __abstract__ = True

    tenant_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )


class TimestampModel(Base):
    """Mixin: created_at + updated_at."""

    __abstract__ = True

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
