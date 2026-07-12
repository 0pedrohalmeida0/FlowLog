"""Lógica de autenticação: valida credenciais, gerencia lockout, abre sessão.

Esta service é o ÚNICO lugar que sabe as regras de lockout. Os feature
modules (login.py) só pedem `autenticar(user, senha)` e tratam as
exceções; não conhecem as regras.
"""

import os
from datetime import datetime

from exceptions import AuthenticationError, ContaBloqueadaError, ValidationError
from logging_config import get_logger
from repositories.usuario_repository import UsuarioRepository
from session import login as session_login
from utils import verificar_senha

logger = get_logger(__name__)


class AuthService:
    """Autenticação com bcrypt + lockout por tentativas falhas.

    Lê as configs `LOCKOUT_MAX_ATTEMPTS` e `LOCKOUT_DURATION_MINUTES` do
    .env (com defaults razoáveis).
    """

    def __init__(self, user_repo: UsuarioRepository | None = None) -> None:
        self._users = user_repo or UsuarioRepository()
        self._max_attempts = int(os.getenv("LOCKOUT_MAX_ATTEMPTS", "5"))
        self._lockout_minutes = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))

    def autenticar(self, username: str, senha: str) -> int:
        """Autentica o usuário e abre a sessão. Retorna o nível de acesso.

        Raises:
            ValidationError: username/senha vazios.
            AuthenticationError: credenciais inválidas (genérico, sem
                distinguir "user não existe" de "senha errada" para
                evitar user enumeration).
            ContaBloqueadaError: conta bloqueada por excesso de tentativas.
        """
        if not username or not senha:
            raise ValidationError("Usuário e senha são obrigatórios.")

        user = self._users.buscar_para_auth(username)

        if not user:
            logger.warning("Login falhou: usuário '%s' não encontrado", username)
            # Mensagem genérica para evitar user enumeration
            raise AuthenticationError("Usuário ou senha incorretos.")

        # Verifica bloqueio ANTES de checar a senha
        bloqueado_ate = user.get("bloqueado_ate")
        if bloqueado_ate and bloqueado_ate > datetime.now():
            restante_min = (bloqueado_ate - datetime.now()).total_seconds() / 60
            restante_int = max(1, int(restante_min) + 1)
            logger.warning(
                "Login bloqueado para '%s' (desbloqueia em ~%d min)",
                username,
                restante_int,
            )
            raise ContaBloqueadaError(
                f"Conta bloqueada por excesso de tentativas. "
                f"Tente novamente em ~{restante_int} min."
            )

        # Verifica senha
        if not verificar_senha(senha, user["senha"]):
            self._tratar_falha(user["id"], username)
            # _tratar_falha() já levantou a exceção apropriada

        # Sucesso
        self._users.resetar_tentativas(user["id"])
        session_login(user["id"], username, user["nivel_acesso"])
        logger.info(
            "Login OK: usuário='%s' id=%d nível=%d",
            username,
            user["id"],
            user["nivel_acesso"],
        )
        return user["nivel_acesso"]

    def _tratar_falha(self, user_id: int, username: str) -> None:
        """Incrementa tentativas, bloqueia se atingiu o limite, levanta exceção."""
        # Lê o estado atual
        user = self._users.buscar_para_auth(username)
        tentativas = (user["tentativas_falhas"] if user else 0) + 1

        self._users.registrar_falha_login(user_id, tentativas)

        if tentativas >= self._max_attempts:
            logger.warning(
                "Conta '%s' BLOQUEADA após %d tentativas falhas (duração: %d min)",
                username,
                tentativas,
                self._lockout_minutes,
            )
            raise ContaBloqueadaError(
                f"Conta bloqueada por {self._lockout_minutes} min após "
                f"{tentativas} tentativas falhas."
            )

        restantes = self._max_attempts - tentativas
        logger.warning(
            "Senha incorreta para '%s' (%d/%d)",
            username,
            tentativas,
            self._max_attempts,
        )
        raise AuthenticationError(
            f"Senha incorreta. {restantes} tentativa(s) " f"restante(s) antes do bloqueio."
        )
