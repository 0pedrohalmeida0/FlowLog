"""Repository para a entidade Usuario.

Operações sensíveis: nunca retorna a coluna `senha` (hash) por padrão.
Use `buscar_para_auth()` apenas em código de autenticação.
"""

from datetime import datetime

from repositories.base import BaseRepository


class UsuarioRepository(BaseRepository):
    _TABLE = "usuarios"

    def buscar_para_auth(self, username: str) -> dict | None:
        """Retorna dados sensíveis (incluindo hash de senha) para autenticação.

        Só deve ser chamado pelo AuthService. Qualquer outro lugar deve usar
        os métodos sem senha.
        """
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT id, username, senha, nivel_acesso, "
                "       tentativas_falhas, bloqueado_ate "
                f"FROM {self._TABLE} WHERE username = %s",
                (username,),
            )
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    def buscar_por_username(self, username: str) -> dict | None:
        """Lookup público (sem senha) para listagens e verificações."""
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT id, username, nivel_acesso, criado_em "
                f"FROM {self._TABLE} WHERE username = %s",
                (username,),
            )
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    def criar(self, username: str, senha_hash: str, nivel_acesso: int) -> int:
        with self.transaction() as (conn, cur):
            cur.execute(
                f"INSERT INTO {self._TABLE} (username, senha, nivel_acesso) " "VALUES (%s, %s, %s)",
                (username, senha_hash, nivel_acesso),
            )
            return cur.lastrowid

    def registrar_falha_login(self, usuario_id: int, tentativas: int) -> None:
        """Incrementa contador de tentativas falhas (ou zera se atingiu limite)."""
        max_attempts = int(__import__("os").getenv("LOCKOUT_MAX_ATTEMPTS", "5"))
        lockout_minutes = int(__import__("os").getenv("LOCKOUT_DURATION_MINUTES", "15"))

        with self.transaction() as (conn, cur):
            if tentativas >= max_attempts:
                from datetime import timedelta

                bloqueado_ate = datetime.now() + timedelta(minutes=lockout_minutes)
                cur.execute(
                    f"UPDATE {self._TABLE} "
                    "SET tentativas_falhas = 0, bloqueado_ate = %s "
                    "WHERE id = %s",
                    (bloqueado_ate, usuario_id),
                )
            else:
                cur.execute(
                    f"UPDATE {self._TABLE} " "SET tentativas_falhas = %s " "WHERE id = %s",
                    (tentativas, usuario_id),
                )

    def resetar_tentativas(self, usuario_id: int) -> None:
        """Zera tentativas falhas e remove bloqueio. Chamado em login bem-sucedido."""
        with self.transaction() as (conn, cur):
            cur.execute(
                f"UPDATE {self._TABLE} "
                "SET tentativas_falhas = 0, bloqueado_ate = NULL "
                "WHERE id = %s",
                (usuario_id,),
            )
