"""Repository para a entidade Produto.

Encapsula todo o SQL que toca `produtos`. Os módulos de feature não
montam SQL diretamente; chamam métodos deste repository.
"""

from repositories.base import BaseRepository


class ProdutoRepository(BaseRepository):
    _TABLE = "produtos"

    def listar_todos(self, empresa_id: int | None = None) -> list[dict]:
        """Retorna todos os produtos (sem join com fornecedor), ordenados por id.

        v1.6: se `empresa_id` for fornecido, filtra por tenant.
        """
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            sql = (
                "SELECT id, empresa_id, nome, quantidade, preco_custo, fornecedor_id, "
                "alerta_minimo, data_entrada "
                f"FROM {self._TABLE}"
            )
            params = []
            if empresa_id is not None:
                sql += " WHERE empresa_id = %s"
                params.append(empresa_id)
            sql += " ORDER BY id ASC"
            cur.execute(sql, tuple(params))
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

    def buscar_por_id_locked(self, produto_id: int, conn, cur) -> dict | None:
        """CR-04: SELECT ... FOR UPDATE dentro de uma transação existente.

        Bloqueia a linha até o fim da transação — impede lost update em
        edições concorrentes. Deve ser chamado com o (conn, cur) de um
        `with self.transaction() as ...` em andamento.
        """
        cur.execute(
            "SELECT id, nome, quantidade, preco_custo, fornecedor_id, "
            "alerta_minimo, data_entrada "
            f"FROM {self._TABLE} WHERE id = %s FOR UPDATE",
            (produto_id,),
        )
        return cur.fetchone()

    def listar_por_fornecedor(
        self, fornecedor_id: int, empresa_id: int | None = None
    ) -> list[dict]:
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            sql = (
                "SELECT id, nome, quantidade, preco_custo, alerta_minimo "
                f"FROM {self._TABLE} WHERE fornecedor_id = %s"
            )
            params = [fornecedor_id]
            if empresa_id is not None:
                sql += " AND empresa_id = %s"
                params.append(empresa_id)
            sql += " ORDER BY nome"
            cur.execute(sql, tuple(params))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def listar_abaixo_do_minimo(self, empresa_id: int | None = None) -> list[dict]:
        """Produtos com quantidade <= alerta_minimo (alerta_minimo não nulo)."""
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            sql = (
                "SELECT p.nome, p.quantidade, p.alerta_minimo, "
                "       COALESCE(f.razao_social, '(sem fornecedor)') AS fornecedor "
                f"FROM {self._TABLE} p "
                "LEFT JOIN fornecedores f ON p.fornecedor_id = f.id "
                "WHERE p.alerta_minimo IS NOT NULL "
                "  AND p.quantidade <= p.alerta_minimo"
            )
            params = []
            if empresa_id is not None:
                sql += " AND p.empresa_id = %s"
                params.append(empresa_id)
            sql += " ORDER BY (p.alerta_minimo - p.quantidade) DESC"
            cur.execute(sql, tuple(params))
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
        empresa_id: int | None = None,  # v1.6
    ) -> int:
        """Insere produto; retorna o id gerado."""
        with self.transaction() as (conn, cur):
            cur.execute(
                f"INSERT INTO {self._TABLE} "
                "(empresa_id, nome, quantidade, preco_custo, fornecedor_id, alerta_minimo) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    empresa_id,
                    nome,
                    quantidade,
                    preco_custo,
                    fornecedor_id,
                    alerta_minimo,
                ),
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
