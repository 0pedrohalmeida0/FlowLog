"""Billing (v2.0 Cloud).

Em v2.0: stub (não chama Stripe/ASAAS real). Interface definida pra
v2.1 trocar pelo provider real sem mudar os routers.
"""

from dataclasses import dataclass
from enum import Enum

from cloud.models import Plano


@dataclass
class PlanoInfo:
    """Metadados de um plano."""

    nome: str
    preco_mensal_brl: float  # em reais
    max_usuarios: int
    max_produtos: int | None  # None = ilimitado
    features: list[str]


PLANOS: dict[Plano, PlanoInfo] = {
    Plano.FREE: PlanoInfo(
        nome="Free",
        preco_mensal_brl=0.0,
        max_usuarios=1,
        max_produtos=100,
        features=[
            "1 usuário admin",
            "Até 100 produtos",
            "Alerta de estoque",
            "Histórico de movimentações",
            "Suporte por comunidade",
        ],
    ),
    Plano.PRO: PlanoInfo(
        nome="Pro",
        preco_mensal_brl=99.0,
        max_usuarios=5,
        max_produtos=None,  # ilimitado
        features=[
            "5 usuários",
            "Produtos ilimitados",
            "Multi-usuário (RBAC)",
            "Export CSV",
            "Suporte por email (24h)",
        ],
    ),
    Plano.BUSINESS: PlanoInfo(
        nome="Business",
        preco_mensal_brl=299.0,
        max_usuarios=50,
        max_produtos=None,
        features=[
            "50 usuários",
            "Produtos ilimitados",
            "API REST completa",
            "Webhooks",
            "Integrações (Zapier, Tiny, Bling)",
            "Suporte prioritário (4h)",
            "White-label",
        ],
    ),
}


def info_plano(plano: Plano) -> PlanoInfo:
    return PLANOS[plano]
