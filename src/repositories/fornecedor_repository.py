"""Repository para a entidade Fornecedor."""

from repositories.base import BaseRepository


class FornecedorRepository(BaseRepository):
    _TABLE = "fornecedores"

    def buscar_por_cnpj(self, cnpj_normalizado: str) -> dict | None:
        """Recebe CNPJ já normalizado (14 dígitos, sem máscara)."""
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT id, razao_social, cnpj "
                f"FROM {self._TABLE} "
                "WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), ' ', '') = %s",
                (cnpj_normalizado,),
            )
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    def buscar_por_id(self, fornecedor_id: int) -> dict | None:
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT id, razao_social, cnpj " f"FROM {self._TABLE} WHERE id = %s",
                (fornecedor_id,),
            )
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    def listar_todos(self) -> list[dict]:
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(f"SELECT id, razao_social, cnpj FROM {self._TABLE} ORDER BY razao_social")
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def criar(self, razao_social: str, cnpj: str) -> int:
        """Insere fornecedor. cnpj deve estar normalizado (14 dígitos)."""
        with self.transaction() as (conn, cur):
            cur.execute(
                f"INSERT INTO {self._TABLE} (razao_social, cnpj) VALUES (%s, %s)",
                (razao_social, cnpj),
            )
            return cur.lastrowid

    def atualizar_razao_social(self, fornecedor_id: int, razao_social: str) -> int:
        with self.transaction() as (conn, cur):
            cur.execute(
                f"UPDATE {self._TABLE} SET razao_social = %s WHERE id = %s",
                (razao_social, fornecedor_id),
            )
            return cur.rowcount

    def excluir(self, fornecedor_id: int) -> int:
        with self.transaction() as (conn, cur):
            cur.execute(
                f"DELETE FROM {self._TABLE} WHERE id = %s",
                (fornecedor_id,),
            )
            return cur.rowcount
