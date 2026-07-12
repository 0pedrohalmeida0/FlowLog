"""Hierarquia de exceções do FlowLog.

Todas as exceções específicas do domínio herdam de `FlowLogError`,
que serve como catch-all em camadas de borda (CLI, API, logging).

Convenção de uso:
    - `ValidationError`       — input do usuário malformado (CNPJ, número, etc).
    - `NotFoundError`         — recurso (produto, fornecedor, usuário) não existe.
    - `DatabaseError`         — falha de I/O com o MySQL.
    - `AuthenticationError`   — credenciais inválidas ou conta bloqueada.
    - `AuthorizationError`    — usuário logado, mas sem permissão (RBAC).
    - `BusinessRuleError`     — viola regra de negócio (ex: estoque negativo).
    - `InfrastructureError`   — falha em camada externa (mysqldump, SMTP, etc).

Os módulos de feature (entrada, saida, etc) devem levantar estas
exceções; o caller (CLI) é responsável por capturá-las e mostrar
mensagens amigáveis.
"""


class FlowLogError(Exception):
    """Erro base do FlowLog. Capture esta para tratar qualquer erro do domínio."""

    def __init__(self, message: str = "") -> None:
        super().__init__(message)
        self.message = message


# ============================================================
# Validação e regras de negócio
# ============================================================


class ValidationError(FlowLogError):
    """Input do usuário malformado (CNPJ, tipo errado, valor inválido, etc)."""


class NotFoundError(FlowLogError):
    """Recurso (produto, fornecedor, usuário, etc) não encontrado."""


class BusinessRuleError(FlowLogError):
    """Operação viola uma regra de negócio do domínio."""


class EstoqueInsuficienteError(BusinessRuleError):
    """Tentativa de saída com quantidade maior que o estoque atual."""


class CNPJInvalidoError(ValidationError):
    """CNPJ fornecido não passa na validação de dígitos verificadores."""


# ============================================================
# Identidade e permissão
# ============================================================


class AuthenticationError(FlowLogError):
    """Falha na autenticação do usuário (credenciais, lockout, etc)."""


class ContaBloqueadaError(AuthenticationError):
    """Conta bloqueada por excesso de tentativas falhas de login."""


class AuthorizationError(FlowLogError):
    """Usuário autenticado, mas sem permissão para a ação solicitada.

    Lançada pelo decorator @requer_nivel e pelas checagens de RBAC
    em services. A CLI mapeia para mensagem amigável + WARNING no log.
    """


# ============================================================
# Infraestrutura
# ============================================================


class DatabaseError(FlowLogError):
    """Falha de comunicação ou query com o MySQL."""


class InfrastructureError(FlowLogError):
    """Falha em camada externa (mysqldump, SMTP, file system, etc)."""
