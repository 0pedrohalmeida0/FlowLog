"""Lógica de movimentação de estoque: entrada e saída com auditoria atômica.

Garante:
    - Transação atômica: UPDATE em `produtos` + INSERT em `historico_movimentacoes`
      na mesma transação, com `SELECT ... FOR UPDATE` para evitar race condition.
    - Validação de quantidade (deve ser > 0).
    - Estoque não pode ficar negativo na saída.
    - usuario_id do registro vem da sessão.
"""

from exceptions import EstoqueInsuficienteError, NotFoundError, ValidationError
from logging_config import get_logger
from repositories.historico_repository import HistoricoRepository
from repositories.produto_repository import ProdutoRepository
from session import usuario_id_atual

logger = get_logger(__name__)


class EstoqueService:
    """Movimentação de estoque: entrada, saída, com auditoria atômica."""

    def __init__(
        self,
        produto_repo: ProdutoRepository | None = None,
        historico_repo: HistoricoRepository | None = None,
    ) -> None:
        self._produtos = produto_repo or ProdutoRepository()
        self._historico = historico_repo or HistoricoRepository()

    def registrar_entrada(self, produto_id: int, quantidade: int) -> dict:
        """Registra uma entrada de estoque.

        Returns:
            dict com produto_id, nome, qtd_anterior, qtd_nova.

        Raises:
            ValidationError: quantidade <= 0.
            NotFoundError: produto não existe.
        """
        self._validar_quantidade(quantidade)
        usuario_id = usuario_id_atual()

        with self._produtos.transaction() as (conn, cur):
            cur.execute(
                "SELECT nome, quantidade FROM produtos WHERE id = %s FOR UPDATE",
                (produto_id,),
            )
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Produto com ID {produto_id} não encontrado.")

            nome, qtd_anterior = row
            qtd_nova = qtd_anterior + quantidade

            cur.execute(
                "UPDATE produtos SET quantidade = %s WHERE id = %s",
                (qtd_nova, produto_id),
            )
            self._historico.inserir(cur, produto_id, "ENTRADA", quantidade, usuario_id)

        logger.info(
            "Entrada: produto_id=%d qtd=+%d usuario_id=%s",
            produto_id,
            quantidade,
            usuario_id,
        )
        return {
            "produto_id": produto_id,
            "nome": nome,
            "qtd_anterior": qtd_anterior,
            "qtd_nova": qtd_nova,
        }

    def registrar_saida(self, produto_id: int, quantidade: int) -> dict:
        """Registra uma saída de estoque.

        Returns:
            dict com produto_id, nome, qtd_anterior, qtd_nova.

        Raises:
            ValidationError: quantidade <= 0.
            NotFoundError: produto não existe.
            EstoqueInsuficienteError: quantidade > saldo atual.
        """
        self._validar_quantidade(quantidade)
        usuario_id = usuario_id_atual()

        with self._produtos.transaction() as (conn, cur):
            cur.execute(
                "SELECT nome, quantidade FROM produtos WHERE id = %s FOR UPDATE",
                (produto_id,),
            )
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Produto com ID {produto_id} não encontrado.")

            nome, qtd_atual = row

            if qtd_atual < quantidade:
                raise EstoqueInsuficienteError(f"Estoque insuficiente! Saldo atual: {qtd_atual}.")

            qtd_nova = qtd_atual - quantidade
            cur.execute(
                "UPDATE produtos SET quantidade = %s WHERE id = %s",
                (qtd_nova, produto_id),
            )
            self._historico.inserir(cur, produto_id, "SAIDA", quantidade, usuario_id)

        logger.info(
            "Saída: produto_id=%d qtd=-%d usuario_id=%s",
            produto_id,
            quantidade,
            usuario_id,
        )
        return {
            "produto_id": produto_id,
            "nome": nome,
            "qtd_anterior": qtd_atual,
            "qtd_nova": qtd_nova,
        }

    @staticmethod
    def _validar_quantidade(quantidade: int) -> None:
        if not isinstance(quantidade, int) or quantidade <= 0:
            raise ValidationError("A quantidade deve ser um inteiro maior que zero.")
