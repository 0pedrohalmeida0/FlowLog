"""Model Branding (v2.1 — white-label completo por tenant).

Cada tenant pode customizar:
    - Logo (URL ou upload como base64)
    - Cor primária
    - Cor de fundo
    - Nome de exibição (mostrado no header em vez de "FlowLog")
    - Domínio custom (CNAME em revenda)
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from cloud.database import Base
from cloud.models.base import TenantScopedModel, gen_uuid


class Branding(TenantScopedModel):
    __tablename__ = "branding"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    # Visual
    nome_exibicao: Mapped[str | None] = mapped_column(String(64), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    cor_primaria: Mapped[str] = mapped_column(String(7), default="#1f6feb", nullable=False)
    cor_fundo: Mapped[str] = mapped_column(String(7), default="#f9fafb", nullable=False)
    cor_texto: Mapped[str] = mapped_column(String(7), default="#111827", nullable=False)

    # Revenda (opcional, v2.1 só guarda; v2.2 implementa CNAME custom)
    dominio_custom: Mapped[str | None] = mapped_column(String(255), nullable=True)

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_css_vars(self) -> dict[str, str]:
        """Retorna CSS custom properties (root vars) pro frontend."""
        return {
            "--flowlog-primary": self.cor_primaria,
            "--flowlog-bg": self.cor_fundo,
            "--flowlog-text": self.cor_texto,
        }
