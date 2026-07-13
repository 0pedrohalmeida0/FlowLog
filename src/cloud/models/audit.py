"""Model AuditoriaAcao (v2.0 Cloud)."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, TypeDecorator, func
from sqlalchemy.dialects.postgresql import JSONB  # type: ignore[attr-defined]
from sqlalchemy.orm import Mapped, mapped_column

from cloud.database import Base
from cloud.models.base import TenantScopedModel, gen_uuid


class JSONBCompat(TypeDecorator):
    """JSONB no Postgres, JSON genérico em outros dialects (SQLite/MySQL)."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


JSONType = JSONBCompat


class AuditoriaAcao(TenantScopedModel):
    __tablename__ = "auditoria_acoes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    usuario_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    acao: Mapped[str] = mapped_column(String(64), nullable=False)
    recurso: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    recurso_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
