"""Model Fornecedor (v2.0 Cloud)."""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from cloud.database import Base
from cloud.models.base import TenantScopedModel, TimestampModel, gen_uuid


class Fornecedor(TenantScopedModel, TimestampModel):
    __tablename__ = "fornecedores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    razao_social: Mapped[str] = mapped_column(String(255), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(14), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    __table_args__ = (
        # CNPJ único por tenant (não global)
        # Implementado via UniqueConstraint
    )

    def __repr__(self) -> str:
        return f"<Fornecedor {self.razao_social}>"
