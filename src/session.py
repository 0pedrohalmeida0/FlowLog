"""Estado da sessão atual: usuário logado, nível, login e última atividade.

Implementação em memória (escopo de processo). Quando o app virar serviço de
longa duração ou ganhar API, isso migra para um storage apropriado
(Redis, JWT, etc.) — o contrato público (login/logout/registrar_atividade/
sessao_expirada/etc.) não muda.
"""

from datetime import datetime

_sessao = {
    "usuario_id": None,
    "username": None,
    "nivel_acesso": None,
    "login_em": None,
    "ultimo_acesso": None,
}


def login(usuario_id, username, nivel_acesso):
    """Registra o usuário logado na sessão atual.

    Inicializa login_em e ultimo_acesso com o mesmo timestamp.
    """
    now = datetime.now()
    _sessao["usuario_id"] = usuario_id
    _sessao["username"] = username
    _sessao["nivel_acesso"] = nivel_acesso
    _sessao["login_em"] = now
    _sessao["ultimo_acesso"] = now


def logout():
    """Limpa a sessão (chamado na saída do sistema ou auto-logout)."""
    for k in _sessao:
        _sessao[k] = None


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


def registrar_atividade():
    """Atualiza o timestamp de última atividade. No-op se não há sessão.

    Chamado em interações do usuário para evitar expiração por inatividade.
    """
    if _sessao["usuario_id"] is not None:
        _sessao["ultimo_acesso"] = datetime.now()


def sessao_expirada(timeout_minutes=30):
    """Retorna True se a sessão está expirada por inatividade.

    - Sem sessão: True (considera expirada).
    - Sem ultimo_acesso registrado: False (acabou de logar).
    - Com ultimo_acesso: True se a diferença agora - ultimo_acesso > timeout.
    """
    if _sessao["usuario_id"] is None:
        return True
    if _sessao.get("ultimo_acesso") is None:
        return False
    elapsed_minutes = (datetime.now() - _sessao["ultimo_acesso"]).total_seconds() / 60
    return elapsed_minutes > timeout_minutes
