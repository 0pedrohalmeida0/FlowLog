"""Decorator @audit para registrar ações no log de auditoria (v1.6).

Uso:
    from audit import audit

    @audit(acao="CREATE", recurso="produto")
    def cadastrar_produto(self, nome, ...):
        ...

    @audit(acao="UPDATE", recurso="produto", extra_fields=["preco_custo", "alerta_minimo"])
    def editar_produto(self, ...):
        ...

Comportamento:
    - Captura automaticamente: usuario_id (sessão), empresa_id (sessão),
      ip, user_agent (sessão).
    - Adiciona um `payload` ao audit: o nome da função + args.
    - Falha de audit NÃO quebra a operação principal (log warning).
    - O `recurso_id` precisa ser extraído — ou do kwarg `id`, ou do
      `return_id=True` no decorator.
"""

import functools
import logging
from collections.abc import Callable
from typing import Any

from database import Database
from repositories.auditoria_repository import AuditoriaRepository
from session import (
    empresa_atual,
    ip_atual,
    user_agent_atual,
    usuario_id_atual,
)

logger = logging.getLogger(__name__)


def audit(
    acao: str,
    recurso: str,
    recurso_id_kwarg: str = "id",
    extra_fields: list[str] | None = None,
    captura_args: bool = True,
) -> Callable:
    """Decorator: registra automaticamente a ação no log de auditoria.

    Args:
        acao: 'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'EXPORT', etc.
        recurso: nome do recurso ('produto', 'fornecedor', etc.)
        recurso_id_kwarg: nome do kwarg que contém o ID do recurso
            (ex: 'produto_id', 'fornecedor_id'). Padrão: 'id'.
        extra_fields: lista de kwargs cujo valor entra no payload.
        captura_args: se True, inclui args/kwargs no payload (default).
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Executa a função primeiro
            try:
                result = func(*args, **kwargs)
            except Exception:
                # Falha na função — não audit (a falha vai pro log normal)
                raise

            # Sucesso: registra a auditoria
            try:
                # Extrai recurso_id do kwarg
                recurso_id = kwargs.get(recurso_id_kwarg)
                if recurso_id is None and args:
                    # Tenta do primeiro arg (self, ...) ou do segundo
                    pass  # fica None

                # Monta payload
                payload: dict[str, Any] = {}
                if captura_args:
                    # Pega só os kwargs (args pode ter o self, evitamos)
                    payload["kwargs"] = {
                        k: v
                        for k, v in kwargs.items()
                        if not k.startswith("_") and k != recurso_id_kwarg
                    }
                if extra_fields:
                    for field in extra_fields:
                        if field in kwargs:
                            payload[field] = kwargs[field]

                # Persiste no banco (transação independente — não conflita)
                db = Database()
                conn = db.connect()
                if not conn:
                    return result
                try:
                    cur = conn.cursor()
                    AuditoriaRepository().registrar(
                        cur,
                        usuario_id=usuario_id_atual(),
                        empresa_id=empresa_atual(),
                        acao=acao,
                        recurso=recurso,
                        recurso_id=recurso_id,
                        ip=ip_atual(),
                        user_agent=user_agent_atual(),
                        payload=payload if payload else None,
                    )
                    conn.commit()
                    cur.close()
                finally:
                    if conn.is_connected():
                        conn.close()
            except Exception as e:
                # Falha de audit NÃO quebra a operação
                logger.warning("Falha ao registrar audit (não-bloqueante): %s", e)

            return result

        return wrapper

    return decorator


def audit_acao_direta(
    acao: str,
    recurso: str,
    recurso_id: int | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    """Registra uma ação de auditoria diretamente (sem decorator).

    Útil pra ações que não cabem num decorator, como LOGIN, LOGOUT,
    EXPORT, etc.
    """
    try:
        db = Database()
        conn = db.connect()
        if not conn:
            return
        try:
            cur = conn.cursor()
            AuditoriaRepository().registrar(
                cur,
                usuario_id=usuario_id_atual(),
                empresa_id=empresa_atual(),
                acao=acao,
                recurso=recurso,
                recurso_id=recurso_id,
                ip=ip_atual(),
                user_agent=user_agent_atual(),
                payload=payload,
            )
            conn.commit()
            cur.close()
        finally:
            if conn.is_connected():
                conn.close()
    except Exception as e:
        logger.warning("Falha ao registrar audit direto: %s", e)
