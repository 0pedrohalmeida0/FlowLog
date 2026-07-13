"""Service layer do FlowLog.

Reexporta as classes principais para uso direto:

    from services import AuthService, EstoqueService, ProdutoService
"""

from services.auth_service import AuthService
from services.empresa_service import EmpresaService
from services.estoque_service import EstoqueService
from services.fornecedor_service import FornecedorService
from services.historico_service import HistoricoService
from services.produto_service import ProdutoService
from services.usuario_service import UsuarioService

__all__ = [
    "AuthService",
    "EmpresaService",  # v1.6 — multi-filial
    "EstoqueService",
    "FornecedorService",
    "HistoricoService",
    "ProdutoService",
    "UsuarioService",
]
