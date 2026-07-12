"""Lógica de consulta do histórico de movimentações (read-only)."""

from repositories.historico_repository import HistoricoRepository


class HistoricoService:
    """Consultas sobre o histórico de movimentações."""

    def __init__(self, repo: HistoricoRepository | None = None) -> None:
        self._repo = repo or HistoricoRepository()

    def listar(
        self,
        tipo: str | None = None,
        limite: int | None = None,
    ) -> list[dict]:
        """Lista movimentações, opcionalmente filtradas por tipo."""
        if tipo and tipo.upper() not in ("ENTRADA", "SAIDA"):
            raise ValueError(f"Tipo inválido: {tipo!r}")
        return self._repo.listar(tipo=tipo.upper() if tipo else None, limite=limite)
