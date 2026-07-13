"""Repository de auditoria (v1.6 — audit log avançado).

Tabela `auditoria_acoes` registra:
    - usuario_id, empresa_id (multi-tenant)
    - acao ('CREATE', 'UPDATE', 'DELETE', 'LOGIN', etc.)
    - recurso ('produto', 'fornecedor', etc.)
    - recurso_id
    - ip, user_agent
    - payload (JSON com dados extras)
    - criado_em

Usado internamente pelo decorator @audit() em src/audit.py.
"""

import json
from datetime import datetime, timedelta
from typing import Any

from repositories.base import BaseRepository


class AuditoriaRepository(BaseRepository):
    _TABLE = "auditoria_acoes"

    def registrar(
        self,
        cursor,
        usuario_id: int | None,
        empresa_id: int | None,
        acao: str,
        recurso: str,
        recurso_id: int | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> int:
        """Registra uma ação de auditoria usando o cursor do chamador.

        Deve ser chamado dentro de uma transação. Retorna o id gerado.
        """
        payload_json = json.dumps(payload, ensure_ascii=False, default=str) if payload else None

        cursor.execute(
            f"INSERT INTO {self._TABLE} "
            "(usuario_id, empresa_id, acao, recurso, recurso_id, ip, user_agent, payload) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (
                usuario_id,
                empresa_id,
                acao,
                recurso,
                recurso_id,
                ip,
                user_agent,
                payload_json,
            ),
        )
        return cursor.lastrowid

    def listar(
        self,
        usuario_id: int | None = None,
        empresa_id: int | None = None,
        recurso: str | None = None,
        recurso_id: int | None = None,
        limite: int = 200,
    ) -> list[dict]:
        """Lista ações de auditoria com filtros opcionais."""
        conn = self._connect()
        try:
            cur = conn.cursor(dictionary=True)
            sql = (
                f"SELECT a.id, a.usuario_id, a.empresa_id, a.acao, a.recurso, "
                f"       a.recurso_id, a.ip, a.user_agent, a.payload, a.criado_em, "
                f"       COALESCE(u.username, '(sistema)') AS username "
                f"FROM {self._TABLE} a "
                f"LEFT JOIN usuarios u ON u.id = a.usuario_id "
                f"WHERE 1=1"
            )
            params: list = []
            if usuario_id is not None:
                sql += " AND a.usuario_id = %s"
                params.append(usuario_id)
            if empresa_id is not None:
                sql += " AND a.empresa_id = %s"
                params.append(empresa_id)
            if recurso:
                sql += " AND a.recurso = %s"
                params.append(recurso)
            if recurso_id is not None:
                sql += " AND a.recurso_id = %s"
                params.append(recurso_id)
            sql += " ORDER BY a.criado_em DESC LIMIT %s"
            params.append(limite)
            cur.execute(sql, tuple(params))
            # Decodifica payload JSON
            rows = cur.fetchall()
            for row in rows:
                if row.get("payload"):
                    try:
                        row["payload"] = json.loads(row["payload"])
                    except (ValueError, TypeError):
                        pass
            return rows
        finally:
            cur.close()
            conn.close()

    def limpar_antigas(self, retencao_dias: int = 365) -> int:
        """Apaga ações mais antigas que `retencao_dias`. Retorna qtd apagada."""
        with self.transaction() as (conn, cur):
            cutoff = datetime.now() - timedelta(days=retencao_dias)
            cur.execute(
                f"DELETE FROM {self._TABLE} WHERE criado_em < %s",
                (cutoff,),
            )
            return cur.rowcount
