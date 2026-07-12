"""Controle de acesso por nível hierárquico (RBAC) e decorator de proteção.

Hierarquia do FlowLog:
    1 = Operador  (apenas leitura e consultas)
    2 = Gerente   (operações de estoque: cadastrar, movimentar, alertas)
    3 = Admin TI  (gestão de usuários e tudo o que o gerente faz)

O decorator @requer_nivel(N) protege uma função exigindo nível >= N.
"""

import logging
from functools import wraps

from session import nivel_atual, usuario_atual, logout


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
                    username, nivel, func.__name__, nivel_minimo,
                )
                print(
                    f"⛔ Acesso Negado: Nível {nivel} insuficiente "
                    f"(requer nível {nivel_minimo})."
                )
                return None

            return func(*args, **kwargs)
        return wrapper
    return decorator
