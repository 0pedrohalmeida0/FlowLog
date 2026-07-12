"""Base para os repositories do FlowLog.

Padrão: cada repository encapsula o SQL de uma "entidade" do domínio
(Produto, Fornecedor, Usuario, etc). Os módulos de feature (entrada.py,
saida_estoque.py, ...) NÃO falam mais diretamente com o banco —
eles chamam métodos de repository, que cuidam de SQL e transações.

Benefícios:
    - SQL vive em um lugar só. Mudar uma coluna = mudar um arquivo.
    - Testes de repository podem mockar a conexão (sem MySQL real).
    - Services podem ser testados com repositories mockados (sem SQL).
    - Feature modules ficam finos (orquestração, não SQL).

Convenções:
    - Métodos retornam `dict | list[dict] | int | None` (nunca tuplas).
    - Métodos que alteram dados NÃO fazem commit — o caller decide.
    - Para operações multi-statement, use o context manager
      `self.transaction()` que cede (conn, cursor) e dá commit/rollback.
    - SQL identifiers (tabelas, colunas) vêm dos atributos da classe
      (`_TABLE`, `_COLUMNS`) para evitar string literals espalhados.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from database import Database
from exceptions import DatabaseError


class BaseRepository:
    """Base comum a todos os repositories."""

    _TABLE: str = ""  # subclasses devem sobrescrever

    def __init__(self, db: Database | None = None) -> None:
        # Permite injetar um Database mockado (testes) sem mexer
        # no singleton de pool. Em produção, deixa None e usa o pool global.
        self.db = db or Database()

    @contextmanager
    def transaction(self) -> Iterator[tuple[object, object]]:
        """Abre transação atômica; commit/rollback/close automáticos.

        Levanta DatabaseError se não conseguir conectar.
        """
        try:
            with self.db.transaction() as (conn, cursor):
                yield conn, cursor
        except ConnectionError as e:
            raise DatabaseError(str(e)) from e

    def _connect(self):
        """Abre conexão simples (para leituras pontuais).

        Retorna a conexão — caller é responsável por fechar com
        conn.close() (que devolve ao pool).
        """
        conn = self.db.connect()
        if conn is None:
            raise DatabaseError("Não foi possível conectar ao banco de dados.")
        return conn
