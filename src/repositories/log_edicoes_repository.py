"""Repository para o histórico de edições de produto (v1.3a)."""

import json

from repositories.base import BaseRepository


class LogEdicoesRepository(BaseRepository):
    _TABLE = "produtos_historico_edicoes"

    def registrar(
        self,
        cursor,
        produto_id: int,
        usuario_id: int | None,
        snapshot_antes: dict,
        snapshot_depois: dict,
    ) -> None:
        """Insere um log de edição dentro de uma transação existente.

        `snapshot_*` são dicts (serão serializados pra JSON).
        """
        cursor.execute(
            f"INSERT INTO {self._TABLE} "
            "(produto_id, usuario_id, snapshot_antes, snapshot_depois) "
            "VALUES (%s, %s, %s, %s)",
            (
                produto_id,
                usuario_id,
                json.dumps(snapshot_antes, ensure_ascii=False),
                json.dumps(snapshot_depois, ensure_ascii=False),
            ),
        )

    def listar_por_produto(self, produto_id: int, limite: int = 50) -> list[dict]:
        """Histórico de edições de um produto, mais recente primeiro."""
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT h.id, h.usuario_id, u.username, "
                "       h.snapshot_antes, h.snapshot_depois, h.data_edicao "
                f"FROM {self._TABLE} h "
                "LEFT JOIN usuarios u ON h.usuario_id = u.id "
                "WHERE h.produto_id = %s "
                "ORDER BY h.data_edicao DESC "
                "LIMIT %s",
                (produto_id, limite),
            )
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()
