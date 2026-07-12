"""Estado da sessão atual: usuário logado, nível de acesso, timestamp de login.

Implementação em memória (escopo de processo). Quando o app virar serviço de
longa duração ou ganhar API, isso migra para um storage apropriado
(Redis, JWT, etc.) — o contrato público (login/logout/usuario_atual/etc.)
não muda.
"""

from datetime import datetime


_sessao = {
    "usuario_id": None,
    "username": None,
    "nivel_acesso": None,
    "login_em": None,
}


def login(usuario_id, username, nivel_acesso):
    """Registra o usuário logado na sessão atual."""
    _sessao["usuario_id"] = usuario_id
    _sessao["username"] = username
    _sessao["nivel_acesso"] = nivel_acesso
    _sessao["login_em"] = datetime.now()


def logout():
    """Limpa a sessão (chamado na saída do sistema)."""
    _sessao["usuario_id"] = None
    _sessao["username"] = None
    _sessao["nivel_acesso"] = None
    _sessao["login_em"] = None


def usuario_atual():
    """Retorna dict com dados do usuário logado, ou None se não logado."""
    if _sessao["usuario_id"] is None:
        return None
    return dict(_sessao)


def usuario_id_atual():
    """Retorna o ID do usuário logado ou None."""
    return _sessao["usuario_id"]


def nivel_atual():
    """Retorna o nível de acesso (1, 2 ou 3) ou None se não logado."""
    return _sessao["nivel_acesso"]


def esta_logado():
    """Retorna True se há usuário logado."""
    return _sessao["usuario_id"] is not None
