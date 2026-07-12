"""Lógica de gestão de usuários: cadastro, listagem.

A parte de autenticação (login/lockout) fica no AuthService.
Aqui é só gestão de cadastro.
"""

from exceptions import ValidationError
from logging_config import get_logger
from repositories.usuario_repository import UsuarioRepository
from utils import hash_senha, validar_senha_complexidade

logger = get_logger(__name__)


# Níveis permitidos: 1 = Operador, 2 = Gerente, 3 = Admin
NIVEIS_PERMITIDOS = {1, 2, 3}


class UsuarioService:
    """Cadastro e gestão de usuários (não inclui autenticação)."""

    def __init__(self, user_repo: UsuarioRepository | None = None) -> None:
        self._users = user_repo or UsuarioRepository()

    def cadastrar(self, username: str, senha: str, nivel_acesso: int) -> int:
        """Cadastra um novo usuário.

        Returns:
            ID do usuário criado.

        Raises:
            ValidationError: username vazio, nível inválido ou senha
                fraca (não atende complexidade).
            CNPJInvalidoError / IntegrityError: username já existe
                (repassado do repository).
        """
        if not username or not username.strip():
            raise ValidationError("O nome de usuário não pode ser vazio.")

        if nivel_acesso not in NIVEIS_PERMITIDOS:
            raise ValidationError(
                f"Nível de acesso inválido: {nivel_acesso}. "
                f"Permitidos: {sorted(NIVEIS_PERMITIDOS)}."
            )

        # CR-03: hash_senha() já aplica o pre-normalizador SHA-256,
        # então senhas arbitrariamente longas funcionam.
        ok, msg = validar_senha_complexidade(senha)
        if not ok:
            raise ValidationError(msg)

        senha_hash = hash_senha(senha).decode("utf-8")
        novo_id = self._users.criar(
            username=username.strip(),
            senha_hash=senha_hash,
            nivel_acesso=nivel_acesso,
        )
        logger.info(
            "Usuário cadastrado: id=%d username='%s' nível=%d",
            novo_id,
            username,
            nivel_acesso,
        )
        return novo_id
