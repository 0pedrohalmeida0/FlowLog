"""Repository para o histórico de movimentações (entradas e saídas)."""

from repositories.base import BaseRepository


class HistoricoRepository(BaseRepository):
    _TABLE = "historico_movimentacoes"

    def listar(self, tipo: str | None = None, limite: int | None = None) -> list[dict]:
        """Lista movimentações, opcionalmente filtradas por tipo ('ENTRADA'/'SAIDA').

        `limite` opcional para não carregar tudo (padrão sem limite).
        Cada row vem com JOIN em produtos (nome) e usuarios (username).
        """
        sql = (
            "SELECT h.id, p.nome AS produto, h.tipo, h.quantidade, "
            "       h.data_movimentacao, "
            "       COALESCE(u.username, '(sistema)') AS usuario "
            f"FROM {self._TABLE} h "
            "JOIN produtos p ON h.produto_id = p.id "
            "LEFT JOIN usuarios u ON h.usuario_id = u.id"
        )
        params: tuple = ()
        if tipo:
            sql += " WHERE UPPER(h.tipo) = %s"
            params = (tipo,)
        sql += " ORDER BY h.data_movimentacao DESC"
        if limite is not None:
            sql += " LIMIT %s"
            params = params + (limite,)

        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, params)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def inserir(
        self,
        cursor,
        produto_id: int,
        tipo: str,
        quantidade: int,
        usuario_id: int | None,
    ) -> None:
        """Insere uma movimentação usando o cursor do chamador.

        NÃO abre conexão própria — deve ser chamado dentro de uma
        transação (cursor do `BaseRepository.transaction()`).
        """
        cursor.execute(
            f"INSERT INTO {self._TABLE} (produto_id, tipo, quantidade, usuario_id) "
            "VALUES (%s, %s, %s, %s)",
            (produto_id, tipo, quantidade, usuario_id),
        )

    def total_saidas_por_produto(self) -> list[dict]:
        """Agregado para a Curva ABC: total de saídas por produto."""
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT p.id AS produto_id, p.nome, "
                "       COALESCE(SUM(h.quantidade), 0) AS total_saidas "
                f"FROM produtos p "
                f"LEFT JOIN {self._TABLE} h "
                "  ON h.produto_id = p.id AND UPPER(h.tipo) = 'SAIDA' "
                "GROUP BY p.id, p.nome"
            )
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()
