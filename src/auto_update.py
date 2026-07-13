"""Checagem de atualização via GitHub Releases.

Estratégia:
    - Consulta https://api.github.com/repos/{owner}/{repo}/releases/latest
    - Compara a tag (sem 'v') com a versão local
    - Se for mais nova, retorna info; senão, None
    - Em background, mostra um aviso no console e prompt pra atualizar

Segurança:
    - Usa HTTPS (api.github.com é confiável)
    - Timeout curto (5s) pra não bloquear o startup
    - Falha silenciosa em rede ruim (log apenas)
"""

import json
import threading
import urllib.error
import urllib.request

from logging_config import get_logger

logger = get_logger(__name__)


GITHUB_API_URL = "https://api.github.com/repos/0pedrohalmeida0/FlowLog/releases/latest"
HTTP_TIMEOUT = 5  # segundos


def _parse_version(tag: str) -> tuple[int, ...]:
    """Converte 'v1.5.0' em (1, 5, 0) pra comparação."""
    clean = tag.lstrip("v").strip()
    partes = clean.split(".")
    nums = []
    for p in partes:
        # Pega só a parte numérica (ignora '-rc1' etc)
        num = ""
        for c in p:
            if c.isdigit():
                num += c
            else:
                break
        nums.append(int(num) if num else 0)
    return tuple(nums)


def _is_newer(remote_tag: str, local_version: str) -> bool:
    """True se remote_tag é mais novo que local_version."""
    try:
        return _parse_version(remote_tag) > _parse_version(local_version)
    except (ValueError, IndexError):
        return False


def checar_atualizacao(local_version: str) -> dict | None:
    """Consulta GitHub Releases e retorna info se houver versão mais nova.

    Args:
        local_version: versão atual (ex: "1.5.0" ou "1.4d")

    Returns:
        Dict com {version, url, notes, published_at} ou None.
    """
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "FlowLog-Updater"},
        )
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        tag = data.get("tag_name", "")
        if not _is_newer(tag, local_version):
            return None

        return {
            "version": tag.lstrip("v"),
            "url": data.get("html_url", ""),
            "notes": (data.get("body") or "")[:500],
            "published_at": data.get("published_at", ""),
            "assets": [a.get("browser_download_url") for a in data.get("assets", [])],
        }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        logger.debug("Falha ao checar update: %s", e)
        return None
    except Exception:
        logger.exception("Erro inesperado em checar_atualizacao")
        return None


def checar_atualizacao_background(local_version: str) -> None:
    """Roda checar_atualizacao em thread separada e mostra aviso se houver.

    Não bloqueia o startup. Em rede ruim, falha silenciosa.
    """

    def worker():
        info = checar_atualizacao(local_version)
        if info is None:
            return
        # Mostra aviso amigável no stderr (não interfere com prints do app)
        print(
            f"\n\033[1;33m🆕 Nova versão disponível: v{info['version']}\033[0m",
            flush=True,
        )
        print(f"   {info['url']}", flush=True)
        print("   Rode `flowlog --check-update` para mais detalhes.\n", flush=True)

    t = threading.Thread(target=worker, daemon=True)
    t.start()
