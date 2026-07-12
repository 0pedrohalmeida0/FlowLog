"""Lógica de produto: cadastro, edição, busca, listagem.

A edição de quantidade NÃO é responsabilidade desta service — alterações
de quantidade devem passar por EstoqueService.entrada/saida para
preservar o histórico de movimentações.
"""

from exceptions import CNPJInvalidoError, NotFoundError, ValidationError
from logging_config import get_logger
from repositories.fornecedor_repository import FornecedorRepository
from repositories.log_edicoes_repository import LogEdicoesRepository
from repositories.produto_repository import ProdutoRepository
from session import usuario_id_atual
from utils import normalize_cnpj, validar_cnpj

logger = get_logger(__name__)


# Campos que podem ser editados (nome, preco, alerta_minimo).
# Quantidade fica de fora de propósito: ela é alterada via entrada/saída
# (EstoqueService) pra preservar o histórico de movimentações.
CAMPOS_EDITAVEIS = {"nome", "preco_custo", "alerta_minimo"}


class ProdutoService:
    """Gestão de produtos: cadastro, edição, listagem."""

    def __init__(
        self,
        produto_repo: ProdutoRepository | None = None,
        fornecedor_repo: FornecedorRepository | None = None,
        log_edicoes_repo: LogEdicoesRepository | None = None,
    ) -> None:
        self._produtos = produto_repo or ProdutoRepository()
        self._fornecedores = fornecedor_repo or FornecedorRepository()
        self._log_edicoes = log_edicoes_repo or LogEdicoesRepository()

    def cadastrar(
        self,
        nome: str,
        quantidade: int,
        preco_custo: float,
        fornecedor_cnpj: str,
        alerta_minimo: int | None = None,
    ) -> int:
        """Cadastra produto. Resolve o fornecedor (cria se não existir).

        Returns:
            ID do produto criado.

        Raises:
            ValidationError: dados faltando ou inválidos.
            CNPJInvalidoError: CNPJ não passa na validação de dígitos.
        """
        if not nome or not nome.strip():
            raise ValidationError("O nome do produto não pode ser vazio.")
        if quantidade < 0:
            raise ValidationError("A quantidade não pode ser negativa.")
        if preco_custo < 0:
            raise ValidationError("O preço de custo não pode ser negativo.")
        if alerta_minimo is not None and alerta_minimo < 0:
            raise ValidationError("O alerta mínimo não pode ser negativo.")
        if not validar_cnpj(fornecedor_cnpj):
            raise CNPJInvalidoError(f"CNPJ inválido: {fornecedor_cnpj!r}. Verifique os dígitos.")

        cnpj = normalize_cnpj(fornecedor_cnpj)

        # Resolve fornecedor (cria se não existir com razao_social padrão)
        fornecedor = self._fornecedores.buscar_por_cnpj(cnpj)
        if fornecedor:
            fornecedor_id = fornecedor["id"]
        else:
            fornecedor_id = self._fornecedores.criar(
                razao_social=f"(cadastro) {cnpj}",
                cnpj=cnpj,
            )
            logger.info("Fornecedor criado: CNPJ=%s id=%d", cnpj, fornecedor_id)

        novo_id = self._produtos.criar(
            nome=nome.strip(),
            quantidade=quantidade,
            preco_custo=preco_custo,
            fornecedor_id=fornecedor_id,
            alerta_minimo=alerta_minimo,
        )
        logger.info("Produto cadastrado: id=%d nome=%s", novo_id, nome)
        return novo_id

    def editar(self, produto_id: int, campos: dict) -> dict:
        """Edita campos permitidos do produto. Grava snapshot antes/depois.

        Returns:
            dict com snapshot_antes e snapshot_depois.

        Raises:
            ValidationError: campos inválidos, tentativa de editar
                campo não permitido (incl. quantidade).
            NotFoundError: produto não existe.
        """
        if not campos:
            raise ValidationError("Nenhum campo fornecido para edição.")

        # Filtra só os campos permitidos; rejeita os que não estão na whitelist
        invalidos = set(campos.keys()) - CAMPOS_EDITAVEIS
        if invalidos:
            raise ValidationError(
                f"Campos não editáveis: {sorted(invalidos)}. "
                f"Permitidos: {sorted(CAMPOS_EDITAVEIS)}. "
                f"Para alterar quantidade, use entrada/saída."
            )

        # Coerção de tipos
        if "nome" in campos:
            if not campos["nome"] or not str(campos["nome"]).strip():
                raise ValidationError("O nome não pode ser vazio.")
            campos["nome"] = str(campos["nome"]).strip()
        if "preco_custo" in campos:
            campos["preco_custo"] = float(campos["preco_custo"])
            if campos["preco_custo"] < 0:
                raise ValidationError("O preço de custo não pode ser negativo.")
        if "alerta_minimo" in campos and campos["alerta_minimo"] is not None:
            campos["alerta_minimo"] = int(campos["alerta_minimo"])
            if campos["alerta_minimo"] < 0:
                raise ValidationError("O alerta mínimo não pode ser negativo.")

        # Lê o produto atual (precisamos do snapshot_antes inteiro).
        # CR-04: o snapshot_antes é só para auditoria; o que importa pra
        # lost-update é o lock na hora do UPDATE, feito dentro da transação.
        atual = self._produtos.buscar_por_id(produto_id)
        if not atual:
            raise NotFoundError(f"Produto com ID {produto_id} não encontrado.")

        snapshot_antes = self._serializar(atual)
        usuario_id = usuario_id_atual()

        with self._produtos.transaction() as (conn, cur):
            # CR-04: SELECT ... FOR UPDATE — bloqueia a linha até o fim
            # da transação, impedindo o cenário de lost-update entre
            # gerentes editando o mesmo produto simultaneamente.
            self._produtos.buscar_por_id_locked(produto_id, conn, cur)

            # UPDATE
            cols = ", ".join(f"{c} = %s" for c in campos)
            valores = list(campos.values()) + [produto_id]
            cur.execute(
                f"UPDATE produtos SET {cols} WHERE id = %s",
                tuple(valores),
            )
            if cur.rowcount == 0:
                # Outra conexão deletou o produto entre o SELECT e o UPDATE
                raise NotFoundError(f"Produto com ID {produto_id} foi removido durante a edição.")

            # Lê o produto depois
            cur.execute(
                "SELECT id, nome, quantidade, preco_custo, fornecedor_id, "
                "alerta_minimo, data_entrada FROM produtos WHERE id = %s",
                (produto_id,),
            )
            novo = cur.fetchone()
            snapshot_depois = self._serializar(novo)

            # Grava snapshot no log de edições
            self._log_edicoes.registrar(
                cur,
                produto_id,
                usuario_id,
                snapshot_antes,
                snapshot_depois,
            )

        logger.info(
            "Produto editado: id=%d campos=%s usuario_id=%s",
            produto_id,
            sorted(campos.keys()),
            usuario_id,
        )
        return {
            "snapshot_antes": snapshot_antes,
            "snapshot_depois": snapshot_depois,
        }

    def buscar(self, produto_id: int) -> dict | None:
        """ME-01: fachada pública para o feature module.

        Substitui o uso direto de `service._produtos.buscar_por_id()`.
        """
        return self._produtos.buscar_por_id(produto_id)

    def listar_todos(self) -> list[dict]:
        """ME-01: fachada pública para o feature module."""
        return self._produtos.listar_todos()

    def listar_abaixo_do_minimo(self) -> list[dict]:
        """Produtos com `quantidade <= alerta_minimo` (alerta_minimo não nulo).

        Cada item: {nome, quantidade, alerta_minimo, fornecedor}.
        """
        return self._produtos.listar_abaixo_do_minimo()

    @staticmethod
    def _serializar(row) -> dict:
        """Converte row do MySQL em dict serializável.

        Aceita tanto dict (dictionary=True cursor) quanto tupla
        (compatibilidade com testes mock).
        """
        if not row:
            return {}
        if isinstance(row, dict):
            return {
                "id": row.get("id"),
                "nome": row.get("nome"),
                "quantidade": row.get("quantidade"),
                "preco_custo": (
                    float(row["preco_custo"]) if row.get("preco_custo") is not None else None
                ),
                "fornecedor_id": row.get("fornecedor_id"),
                "alerta_minimo": row.get("alerta_minimo"),
            }
        # Tupla (formato legado)
        return {
            "id": row[0],
            "nome": row[1],
            "quantidade": row[2],
            "preco_custo": float(row[3]) if row[3] is not None else None,
            "fornecedor_id": row[4],
            "alerta_minimo": row[5],
        }
