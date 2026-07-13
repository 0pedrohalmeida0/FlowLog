"""Service de gestão de empresas (v1.6 — multi-filial).

Responsabilidades:
- CRUD de empresas (com validação de CNPJ)
- Vincular/desvincular usuários a empresas (com nível)
- Listar empresas do usuário logado
- Trocar empresa atual na sessão
"""

from exceptions import NotFoundError, ValidationError
from logging_config import get_logger
from repositories.empresa_repository import EmpresaRepository
from session import (
    setar_empresa_atual,
    usuario_id_atual,
)
from utils import normalize_cnpj, validar_cnpj

logger = get_logger(__name__)


NIVEIS_VALIDOS = {1, 2, 3}


class EmpresaService:
    """Gestão de empresas e vínculos com usuários."""

    def __init__(self, empresa_repo: EmpresaRepository | None = None) -> None:
        self._empresas = empresa_repo or EmpresaRepository()

    def cadastrar(
        self,
        cnpj: str,
        razao_social: str,
        nome_fantasia: str | None = None,
    ) -> int:
        """Cadastra uma nova empresa (filial).

        Raises:
            ValidationError: CNPJ inválido, razao_social vazio.
        """
        if not validar_cnpj(cnpj):
            raise ValidationError(f"CNPJ inválido: {cnpj!r}")
        cnpj_norm = normalize_cnpj(cnpj)
        if not razao_social or not razao_social.strip():
            raise ValidationError("Razão social não pode ser vazia.")

        # Verifica duplicata
        if self._empresas.buscar_por_cnpj(cnpj_norm) is not None:
            raise ValidationError(f"Já existe empresa com CNPJ {cnpj_norm}.")

        novo_id = self._empresas.criar(
            cnpj=cnpj_norm,
            razao_social=razao_social.strip(),
            nome_fantasia=(nome_fantasia.strip() if nome_fantasia else None),
        )
        logger.info(
            "Empresa cadastrada: id=%d cnpj=%s razao=%s",
            novo_id,
            cnpj_norm,
            razao_social,
        )
        return novo_id

    def listar(self, apenas_ativas: bool = True) -> list[dict]:
        return self._empresas.listar(apenas_ativas=apenas_ativas)

    def desativar(self, empresa_id: int) -> None:
        rc = self._empresas.desativar(empresa_id)
        if rc == 0:
            raise NotFoundError(f"Empresa com ID {empresa_id} não encontrada.")
        logger.info("Empresa desativada: id=%d", empresa_id)

    def reativar(self, empresa_id: int) -> None:
        rc = self._empresas.reativar(empresa_id)
        if rc == 0:
            raise NotFoundError(f"Empresa com ID {empresa_id} não encontrada.")
        logger.info("Empresa reativada: id=%d", empresa_id)

    # ---- vínculos usuário ↔ empresa ----

    def empresas_do_usuario(self, usuario_id: int) -> list[dict]:
        return self._empresas.empresas_do_usuario(usuario_id)

    def adicionar_usuario(self, usuario_id: int, empresa_id: int, nivel: int) -> None:
        """Vincula usuário a empresa com determinado nível (1, 2 ou 3)."""
        if nivel not in NIVEIS_VALIDOS:
            raise ValidationError(f"Nível inválido: {nivel}. Use 1, 2 ou 3.")
        self._empresas.adicionar_usuario(usuario_id, empresa_id, nivel)
        logger.info(
            "Usuário %d vinculado à empresa %d com nível %d",
            usuario_id,
            empresa_id,
            nivel,
        )

    def remover_usuario(self, usuario_id: int, empresa_id: int) -> None:
        rc = self._empresas.remover_usuario(usuario_id, empresa_id)
        if rc == 0:
            raise NotFoundError(f"Vínculo usuário {usuario_id} / empresa {empresa_id} não existe.")

    # ---- troca de empresa atual na sessão ----

    def selecionar_empresa(self, empresa_id: int) -> dict:
        """Define a empresa atual na sessão. Retorna info da empresa.

        Raises:
            NotFoundError: usuário não tem acesso a essa empresa.
        """
        uid = usuario_id_atual()
        if uid is None:
            raise NotFoundError("Nenhum usuário logado.")

        nivel = self._empresas.nivel_usuario(uid, empresa_id)
        if nivel is None:
            raise NotFoundError(
                f"Você não tem acesso à empresa {empresa_id}. " f"Peça ao admin pra te vincular."
            )

        # Pega dados da empresa
        empresas = self._empresas.empresas_do_usuario(uid)
        empresa = next((e for e in empresas if e["id"] == empresa_id), None)
        if empresa is None:
            raise NotFoundError(f"Empresa {empresa_id} não encontrada ou inativa.")

        setar_empresa_atual(empresa_id, nivel)
        logger.info(
            "Usuário %d selecionou empresa %d (nível %d)",
            uid,
            empresa_id,
            nivel,
        )
        return empresa

    def auto_selecionar_se_unica(self) -> bool:
        """Se o usuário tem acesso a exatamente 1 empresa, seleciona ela.

        Retorna True se selecionou, False caso contrário (zero ou múltiplas).
        """
        uid = usuario_id_atual()
        if uid is None:
            return False
        empresas = self._empresas.empresas_do_usuario(uid)
        if len(empresas) == 1:
            setar_empresa_atual(empresas[0]["id"], empresas[0]["nivel_empresa"])
            return True
        return False
