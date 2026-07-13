"""Repository para a entidade Empresa (v1.6 — multi-filial)."""

from repositories.base import BaseRepository


class EmpresaRepository(BaseRepository):
    _TABLE = "empresas"

    def buscar_por_cnpj(self, cnpj: str) -> dict | None:
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                f"SELECT id, cnpj, razao_social, nome_fantasia, ativa "
                f"FROM {self._TABLE} WHERE cnpj = %s",
                (cnpj,),
            )
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    def listar(self, apenas_ativas: bool = True) -> list[dict]:
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            sql = (
                f"SELECT id, cnpj, razao_social, nome_fantasia, ativa, criado_em "
                f"FROM {self._TABLE}"
            )
            if apenas_ativas:
                sql += " WHERE ativa = TRUE"
            sql += " ORDER BY razao_social"
            cur.execute(sql)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def criar(self, cnpj: str, razao_social: str, nome_fantasia: str | None = None) -> int:
        with self.transaction() as (conn, cur):
            cur.execute(
                f"INSERT INTO {self._TABLE} (cnpj, razao_social, nome_fantasia) "
                "VALUES (%s, %s, %s)",
                (cnpj, razao_social, nome_fantasia),
            )
            return cur.lastrowid

    def desativar(self, empresa_id: int) -> int:
        """Marca empresa como inativa (soft delete)."""
        with self.transaction() as (conn, cur):
            cur.execute(
                f"UPDATE {self._TABLE} SET ativa = FALSE WHERE id = %s",
                (empresa_id,),
            )
            return cur.rowcount

    def reativar(self, empresa_id: int) -> int:
        with self.transaction() as (conn, cur):
            cur.execute(
                f"UPDATE {self._TABLE} SET ativa = TRUE WHERE id = %s",
                (empresa_id,),
            )
            return cur.rowcount

    def nivel_usuario(self, usuario_id: int, empresa_id: int) -> int | None:
        """Retorna o nível do usuário na empresa (1, 2, 3) ou None se não tem acesso."""
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT nivel_empresa FROM usuarios_empresas "
                "WHERE usuario_id = %s AND empresa_id = %s",
                (usuario_id, empresa_id),
            )
            row = cur.fetchone()
            return row["nivel_empresa"] if row else None
        finally:
            cur.close()
            conn.close()

    def empresas_do_usuario(self, usuario_id: int) -> list[dict]:
        """Lista empresas onde o usuário tem algum nível."""
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT e.id, e.cnpj, e.razao_social, e.nome_fantasia, "
                "       ue.nivel_empresa "
                "FROM empresas e "
                "JOIN usuarios_empresas ue ON ue.empresa_id = e.id "
                "WHERE ue.usuario_id = %s AND e.ativa = TRUE "
                "ORDER BY e.razao_social",
                (usuario_id,),
            )
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def adicionar_usuario(self, usuario_id: int, empresa_id: int, nivel: int) -> None:
        """Vincula um usuário a uma empresa com determinado nível."""
        with self.transaction() as (conn, cur):
            cur.execute(
                "INSERT INTO usuarios_empresas (usuario_id, empresa_id, nivel_empresa) "
                "VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE nivel_empresa = VALUES(nivel_empresa)",
                (usuario_id, empresa_id, nivel),
            )

    def remover_usuario(self, usuario_id: int, empresa_id: int) -> int:
        with self.transaction() as (conn, cur):
            cur.execute(
                "DELETE FROM usuarios_empresas " "WHERE usuario_id = %s AND empresa_id = %s",
                (usuario_id, empresa_id),
            )
            return cur.rowcount
