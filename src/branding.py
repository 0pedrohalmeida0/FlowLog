"""White-label (v1.6 — Licença + Premium).

Permite customizar logo, cores e nome do cliente em relatórios
exportados (CSV, dashboard). Configurado em `branding.json` no
diretório de configuração do FlowLog.

Estrutura do branding.json (opcional):

    {
        "empresa_display": "Minha Empresa LTDA",
        "cor_primaria": "#0066CC",
        "cor_secundaria": "#333333",
        "logo_path": "C:/path/logo.png",   // opcional
        "relatorio_rodape": "Confidencial — uso interno"
    }

Se o arquivo não existir, usa defaults (FlowLog genérico).
"""

import json
import os
from pathlib import Path
from typing import Any

from logging_config import get_logger
from repositories.empresa_repository import EmpresaRepository
from session import empresa_atual

logger = get_logger(__name__)


def _get_empresa_info(empresa_id: int) -> dict | None:
    """Helper: busca info de uma empresa (cache-friendly para branding)."""
    try:
        conn = EmpresaRepository()._connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT id, cnpj, razao_social, nome_fantasia FROM empresas WHERE id = %s",
                (empresa_id,),
            )
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        logger.debug("Falha ao buscar empresa %d: %s", empresa_id, e)
        return None


DEFAULTS: dict[str, Any] = {
    "empresa_display": "FlowLog",
    "cor_primaria": "#1f6feb",
    "cor_secundaria": "#586069",
    "logo_path": None,
    "relatorio_rodape": "",
}


def _branding_path() -> Path:
    """Caminho do branding.json. Por plataforma."""
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "FlowLog" / "branding.json"
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "flowlog" / "branding.json"


def carregar_branding() -> dict[str, Any]:
    """Carrega branding do disco. Defaults se não existir."""
    path = _branding_path()
    if not path.exists():
        return dict(DEFAULTS)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        # Merge com defaults
        merged = dict(DEFAULTS)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("branding.json corrompido: %s", e)
        return dict(DEFAULTS)


def salvar_branding(branding: dict[str, Any]) -> None:
    """Persiste branding no disco."""
    path = _branding_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(branding, f, indent=2, ensure_ascii=False)
    logger.info("Branding salvo em %s", path)


def branding_efetivo() -> dict[str, Any]:
    """Branding efetivo: o do disco, com fallback pra nome da empresa atual."""
    b = carregar_branding()
    # Se empresa_display ainda é o default "FlowLog" e tem empresa selecionada,
    # usa o nome da empresa como display
    if b.get("empresa_display") == "FlowLog":
        emp_id = empresa_atual()
        if emp_id is not None:
            emp = _get_empresa_info(emp_id)
            if emp:
                b["empresa_display"] = emp.get("razao_social", "FlowLog")
                if not b.get("logo_path"):
                    # Tenta achar logo_<cnpj>.png no mesmo dir
                    pass
    return b


def aplicar_rodape(texto: str) -> str:
    """Adiciona o rodapé customizado em relatório (se configurado)."""
    b = branding_efetivo()
    rodape = b.get("relatorio_rodape", "")
    if rodape:
        return f"{texto}\n\n---\n{rodape}\n"
    return texto
