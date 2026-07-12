"""Lógica de fornecedor: cadastro, edição, exclusão, busca por CNPJ."""

from exceptions import CNPJInvalidoError, NotFoundError, ValidationError
from logging_config import get_logger
from repositories.fornecedor_repository import FornecedorRepository
from utils import normalize_cnpj, validar_cnpj

logger = get_logger(__name__)


class FornecedorService:
    """Gestão de fornecedores: cadastro, edição, exclusão, listagem."""

    def __init__(self, repo: FornecedorRepository | None = None) -> None:
        self._repo = repo or FornecedorRepository()

    def cadastrar(self, razao_social: str, cnpj: str) -> int:
        """Cadastra fornecedor (CNPJ normalizado)."""
        if not razao_social or not razao_social.strip():
            raise ValidationError("A razão social não pode ser vazia.")
        if not validar_cnpj(cnpj):
            raise CNPJInvalidoError(f"CNPJ inválido: {cnpj!r}.")

        cnpj_norm = normalize_cnpj(cnpj)

        # Verifica se já existe
        if self._repo.buscar_por_cnpj(cnpj_norm):
            raise ValidationError(f"Fornecedor com CNPJ {cnpj_norm} já está cadastrado.")

        novo_id = self._repo.criar(razao_social.strip(), cnpj_norm)
        logger.info("Fornecedor cadastrado: id=%d cnpj=%s", novo_id, cnpj_norm)
        return novo_id

    def editar_razao_social(self, fornecedor_id: int, nova_razao: str) -> None:
        """Atualiza apenas a razão social."""
        if not nova_razao or not nova_razao.strip():
            raise ValidationError("A razão social não pode ser vazia.")

        rc = self._repo.atualizar_razao_social(fornecedor_id, nova_razao.strip())
        if rc == 0:
            raise NotFoundError(f"Fornecedor com ID {fornecedor_id} não encontrado.")
        logger.info("Fornecedor ID=%d: razão social atualizada", fornecedor_id)

    def excluir(self, fornecedor_id: int) -> None:
        """Exclui fornecedor. Pode falhar com FK se houver produtos vinculados."""
        rc = self._repo.excluir(fornecedor_id)
        if rc == 0:
            raise NotFoundError(f"Fornecedor com ID {fornecedor_id} não encontrado.")
        logger.info("Fornecedor ID=%d excluído", fornecedor_id)
