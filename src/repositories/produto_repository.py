"""Repository para a entidade Produto.

Encapsula todo o SQL que toca `produtos`. Os módulos de feature não
montam SQL diretamente; chamam métodos deste repository.
"""

from repositories.base import BaseRepository


class ProdutoRepository(BaseRepository):
    _TABLE = "produtos"

    def listar_todos(self) -> list[dict]:
        """Retorna todos os produtos (sem join com fornecedor)."""
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT id, nome, quantidade, preco_custo, fornecedor_id, "
                "alerta_minimo, data_entrada "
                f"FROM {self._TABLE} ORDER BY id"
            )
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def buscar_por_id(self, produto_id: int) -> dict | None:
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT id, nome, quantidade, preco_custo, fornecedor_id, "
                "alerta_minimo, data_entrada "
                f"FROM {self._TABLE} WHERE id = %s",
                (produto_id,),
            )
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    def listar_por_fornecedor(self, fornecedor_id: int) -> list[dict]:
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT id, nome, quantidade, preco_custo, alerta_minimo "
                f"FROM {self._TABLE} WHERE fornecedor_id = %s ORDER BY nome",
                (fornecedor_id,),
            )
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def listar_abaixo_do_minimo(self) -> list[dict]:
        """Produtos com quantidade <= alerta_minimo (alerta_minimo não nulo)."""
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT p.nome, p.quantidade, p.alerta_minimo, "
                "       COALESCE(f.razao_social, '(sem fornecedor)') AS fornecedor "
                f"FROM {self._TABLE} p "
                "LEFT JOIN fornecedores f ON p.fornecedor_id = f.id "
                "WHERE p.alerta_minimo IS NOT NULL "
                "  AND p.quantidade <= p.alerta_minimo "
                "ORDER BY (p.alerta_minimo - p.quantidade) DESC"
            )
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def criar(
        self,
        nome: str,
        quantidade: int,
        preco_custo: float,
        fornecedor_id: int | None,
        alerta_minimo: int | None,
    ) -> int:
        """Insere produto; retorna o id gerado."""
        with self.transaction() as (conn, cur):
            cur.execute(
                f"INSERT INTO {self._TABLE} "
                "(nome, quantidade, preco_custo, fornecedor_id, alerta_minimo) "
                "VALUES (%s, %s, %s, %s, %s)",
                (nome, quantidade, preco_custo, fornecedor_id, alerta_minimo),
            )
            return cur.lastrowid

    def atualizar_campos(self, produto_id: int, campos: dict) -> int:
        """Atualiza apenas os campos fornecidos no dict.

        Retorna rowcount (0 se id não existe, 1 se atualizou).
        Não permite atualizar `id` (chave primária).
        """
        if not campos:
            return 0
        # Segurança: nunca deixa atualizar a PK
        campos.pop("id", None)

        cols = ", ".join(f"{c} = %s" for c in campos)
        valores = list(campos.values()) + [produto_id]
        with self.transaction() as (conn, cur):
            cur.execute(
                f"UPDATE {self._TABLE} SET {cols} WHERE id = %s",
                tuple(valores),
            )
            return cur.rowcount

    def ajustar_quantidade(self, produto_id: int, nova_quantidade: int) -> int:
        """Define a quantidade absoluta (cuidado: não registra log de movimento).

        Para operações normais, prefira `services.EstoqueService.entrada/saida`
        que cuidam do log de histórico. Este método é para correção administrativa
        sem log (caso a auditoria seja feita por outro mecanismo).
        """
        with self.transaction() as (conn, cur):
            cur.execute(
                f"UPDATE {self._TABLE} SET quantidade = %s WHERE id = %s",
                (nova_quantidade, produto_id),
            )
            return cur.rowcount
