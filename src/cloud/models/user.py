"""Model User (v2.1 Cloud).

Usuários pertencem a tenants. Cada user tem 1 tenant (single-tenant
no nível de user; o tenant é multi-user).

v2.1: campo `super_admin` pra operadores globais do SaaS.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cloud.database import Base
from cloud.models.base import gen_uuid

if TYPE_CHECKING:
    from cloud.models.tenant import Tenant


class NivelAcesso(str, PyEnum):
    OPERADOR = "1"
    GERENTE = "2"
    ADMIN = "3"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    senha_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Google SSO: preenche quando o user se autentica via Google pela primeira vez
    google_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    nivel_acesso: Mapped[NivelAcesso] = mapped_column(
        Enum(NivelAcesso, native_enum=False, length=16),
        default=NivelAcesso.OPERADOR,
        nullable=False,
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Super admin global: enxerga todos os tenants, pode mexer em billing,
    # suspender contas, ver MRR. Usuários normais (tenant users) têm False.
    super_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships com lazy='raise' (impede lazy load async implícito)
    tenant: Mapped["Tenant"] = relationship(
        lazy="raise",
        viewonly=True,
        foreign_keys=[tenant_id],
    )
    tenant_obj: Mapped["Tenant"] = relationship(
        back_populates="users",
        lazy="raise",
        viewonly=True,
        foreign_keys=[tenant_id],
    )

    def __repr__(self) -> str:
        return f"<User {self.email} (tenant={self.tenant_id[:8]})>"
