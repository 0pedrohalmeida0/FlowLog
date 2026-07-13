"""Controle de acesso por nível hierárquico (RBAC) e decorator de proteção.

Hierarquia do FlowLog:
    1 = Operador  (apenas leitura e consultas)
    2 = Gerente   (operações de estoque: cadastrar, movimentar, alertas)
    3 = Admin TI  (gestão de usuários e tudo o que o gerente faz)

O decorator @requer_nivel(N) protege uma função exigindo nível >= N.

v1.6 — multi-filial:
    O decorator @requer_nivel_empresa(N) exige que o usuário tenha nível >= N
    NA EMPRESA ATUAL (session.empresa_atual()), não no global.
    Usado em feature modules que operam no contexto de uma filial.
"""

import logging
from functools import wraps

from session import (
    empresa_atual,
    logout,
    nivel_atual,
    nivel_empresa_atual,
    usuario_atual,
)

logger = logging.getLogger(__name__)


def requer_nivel(nivel_minimo):
    """Decorator que exige um nível de acesso mínimo para executar a função.

    Uso:
        @requer_nivel(2)
        def cadastrar_produto():
            ...

    Comportamento:
        - Sem sessão ativa: imprime aviso, limpa sessão, retorna None.
        - Nível insuficiente: registra WARNING no log, imprime aviso, retorna None.
        - Nível suficiente: executa a função normalmente.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nivel = nivel_atual()

            if nivel is None:
                print("⛔ Sessão expirada. Faça login novamente.")
                logout()
                return None

            if nivel < nivel_minimo:
                user = usuario_atual() or {}
                username = user.get("username", "?")
                logger.warning(
                    "Acesso NEGADO: usuário '%s' (nível %d) tentou '%s' (requer nível %d)",
                    username,
                    nivel,
                    func.__name__,
                    nivel_minimo,
                )
                print(
                    f"⛔ Acesso Negado: Nível {nivel} insuficiente "
                    f"(requer nível {nivel_minimo})."
                )
                return None

            return func(*args, **kwargs)

        return wrapper

    return decorator


def requer_nivel_empresa(nivel_minimo):
    """Decorator (v1.6): exige nível mínimo NA EMPRESA ATUAL.

    Diferente de @requer_nivel que usa o nível global, este usa o nível
    específico do usuário NESTA empresa (pode ser menor ou maior que o global).

    Regras:
        - Sem empresa selecionada: retorna None (imprime aviso).
        - Nível na empresa < mínimo: registra WARNING + retorna None.
        - OK: executa a função.

    Uso:
        @requer_nivel_empresa(2)
        def cadastrar_produto_da_filial():
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            emp_id = empresa_atual()
            if emp_id is None:
                print("⛔ Nenhuma filial selecionada. Selecione uma filial primeiro.")
                logger.warning(
                    "Acesso NEGADO: '%s' sem empresa selecionada",
                    func.__name__,
                )
                return None

            nivel = nivel_empresa_atual()
            if nivel is None:
                print("⛔ Você não tem acesso a esta filial.")
                logger.warning(
                    "Acesso NEGADO: '%s' sem nível na empresa %s",
                    func.__name__,
                    emp_id,
                )
                return None

            if nivel < nivel_minimo:
                user = usuario_atual() or {}
                username = user.get("username", "?")
                logger.warning(
                    "Acesso NEGADO: '%s' (nível %d na empresa %d) tentou '%s' (requer %d)",
                    username,
                    nivel,
                    emp_id,
                    func.__name__,
                    nivel_minimo,
                )
                print(
                    f"⛔ Acesso Negado: Nível {nivel} insuficiente na filial atual "
                    f"(requer {nivel_minimo})."
                )
                return None

            return func(*args, **kwargs)

        return wrapper

    return decorator
