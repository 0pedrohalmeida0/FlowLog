"""Backup e restauração do banco MySQL via mysqldump.

Fluxo:
    1. `fazer_backup()`: roda mysqldump e salva em ./backups/
       com nome timestamped.
    2. `listar_backups()`: mostra os backups disponíveis.
    3. `restaurar_backup(path)`: roda mysql < backup.sql.

Requer:
    - mysqldump e mysql disponíveis no PATH (instalados junto com MySQL).
    - Permissão de leitura no diretório de saída.
    - Permissão de escrita no banco para o restore (cuidado: apaga dados).

Diretório de backups: ./backups/ relativo ao cwd. Em produção (v1.5
com instalador), vai para %APPDATA%/FlowLog/backups/ no Windows.
"""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from logging_config import get_logger

logger = get_logger(__name__)


BACKUP_DIR = Path("backups")
MAX_BACKUPS_RELOCALES = 30  # retenção padrão (legado); v1.4c lê de env


def _max_backups():
    """ME-03: retenção lida do env (BACKUP_MAX_RETENTION), default 30.

    Configurável via .env. Aceita 0 = sem retenção (não remove nada).
    """
    try:
        return int(os.getenv("BACKUP_MAX_RETENTION", "30"))
    except ValueError:
        return 30


# ============================================================
# Helpers
# ============================================================


def _verificar_binarios():
    """Garante que mysqldump e mysql estão no PATH."""
    for bin_name in ("mysqldump", "mysql"):
        if shutil.which(bin_name) is None:
            raise RuntimeError(
                f"'{bin_name}' não encontrado no PATH. "
                f"Instale o cliente MySQL ou verifique o PATH."
            )


def _ler_credenciais():
    """Lê credenciais do .env (via load_dotenv no database.py já importado)."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "flowlog"),
    }


# ============================================================
# Backup
# ============================================================


def fazer_backup():
    """Gera um dump completo do banco e salva em ./backups/.

    Returns:
        Path do arquivo gerado.
    """
    try:
        _verificar_binarios()
    except RuntimeError as e:
        print(f"❌ {e}")
        return None

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = BACKUP_DIR / f"flowlog_backup_{ts}.sql"

    creds = _ler_credenciais()
    # CR-01: a senha é passada via env var (MYSQL_PWD) em vez de -p{senha}
    # na linha de comando. -p{senha} aparece em 'ps aux' e em logs do SO.
    env = os.environ.copy()
    if creds["password"]:
        env["MYSQL_PWD"] = creds["password"]
    cmd = [
        "mysqldump",
        "-h",
        creds["host"],
        "-u",
        creds["user"],
        "--single-transaction",  # garante consistência sem lock
        "--routines",  # inclui stored procedures (preparação futura)
        "--triggers",  # inclui triggers
        creds["database"],
    ]

    try:
        with open(filename, "w", encoding="utf-8") as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=False, env=env)
        # Limpa a senha do ambiente local (defesa em profundidade)
        env.pop("MYSQL_PWD", None)

        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="ignore")
            logger.error("mysqldump falhou: %s", stderr)
            print(f"❌ mysqldump falhou: {stderr}")
            # Remove arquivo vazio/quebrado
            if filename.exists() and filename.stat().st_size == 0:
                filename.unlink()
            return None

        size_kb = filename.stat().st_size / 1024
        logger.info("Backup criado: %s (%.1f KB)", filename, size_kb)
        print(f"✅ Backup criado: {filename}  ({size_kb:.1f} KB)")

        # Limpa backups antigos além da retenção
        _apagar_backups_antigos()
        return filename

    except Exception as e:
        logger.exception("Erro ao gerar backup")
        print(f"❌ Erro ao gerar backup: {e}")
        return None


def _apagar_backups_antigos():
    """ME-03: apaga os backups mais antigos além de _max_backups() (env)."""
    if not BACKUP_DIR.exists():
        return
    limite = _max_backups()
    if limite <= 0:
        return  # retenção desabilitada
    backups = sorted(
        BACKUP_DIR.glob("flowlog_backup_*.sql"),
        key=lambda p: p.stat().st_mtime,
    )
    while len(backups) > limite:
        antigo = backups.pop(0)
        try:
            antigo.unlink()
            logger.info("Backup antigo removido: %s", antigo)
        except OSError as e:
            logger.warning("Não foi possível remover backup antigo %s: %s", antigo, e)


def listar_backups():
    """Mostra os backups disponíveis em ./backups/."""
    if not BACKUP_DIR.exists():
        print(f"⚠️ Nenhum backup encontrado. Diretório '{BACKUP_DIR}' não existe.")
        print("   (use a opção de backup para criar o primeiro)")
        return []

    backups = sorted(
        BACKUP_DIR.glob("flowlog_backup_*.sql"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,  # mais recente primeiro
    )

    if not backups:
        print(f"⚠️ Nenhum backup encontrado em '{BACKUP_DIR}'.")
        return []

    print(f"\n--- 💾 BACKUPS DISPONÍVEIS ({len(backups)}) ---")
    print(f"{'#':<3} | {'ARQUIVO':<40} | {'TAMANHO':>10} | {'DATA':<16}")
    print("-" * 80)
    for i, b in enumerate(backups, start=1):
        size_kb = b.stat().st_size / 1024
        mtime = datetime.fromtimestamp(b.stat().st_mtime)
        print(
            f"{i:<3} | {b.name:<40} | {size_kb:>8.1f} KB | {mtime.strftime('%Y-%m-%d %H:%M'):<16}"
        )
    print("-" * 80)
    return backups


# ============================================================
# Restauração
# ============================================================


def restaurar_backup(caminho=None):
    """Restaura um backup no banco atual.

    CUIDADO: isso apaga os dados atuais e substitui pelo conteúdo do backup.

    Args:
        caminho: Path do .sql. Se None, pergunta ao usuário.
    """
    try:
        _verificar_binarios()
    except RuntimeError as e:
        print(f"❌ {e}")
        return

    if caminho is None:
        backups = listar_backups()
        if not backups:
            return
        escolha = input("\nNúmero do backup para restaurar (ou 'C' para cancelar): ").strip()
        if escolha.upper() == "C":
            print("Restauração cancelada.")
            return
        try:
            idx = int(escolha) - 1
            caminho = backups[idx]
        except (ValueError, IndexError):
            print("❌ Escolha inválida.")
            return

    caminho = Path(caminho)
    if not caminho.exists():
        print(f"❌ Arquivo não encontrado: {caminho}")
        return

    # Aviso de perigo
    print("\n⚠️  ATENÇÃO: a restauração vai SUBSTITUIR todos os dados atuais do banco")
    print(f"    pelo conteúdo de: {caminho}")
    confirma1 = input("    Tem certeza? Digite 'RESTAURAR' para confirmar: ").strip()
    if confirma1 != "RESTAURAR":
        print("Restauração cancelada.")
        return

    creds = _ler_credenciais()
    # CR-01: idem — senha via MYSQL_PWD, não em argv
    env = os.environ.copy()
    if creds["password"]:
        env["MYSQL_PWD"] = creds["password"]
    cmd = [
        "mysql",
        "-h",
        creds["host"],
        "-u",
        creds["user"],
        creds["database"],
    ]

    try:
        with open(caminho, encoding="utf-8") as f:
            result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, check=False, env=env)
        env.pop("MYSQL_PWD", None)

        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="ignore")
            logger.error("mysql restore falhou: %s", stderr)
            print(f"❌ mysql restore falhou: {stderr}")
            return

        logger.info("Backup restaurado de: %s", caminho)
        print(f"✅ Backup restaurado com sucesso de: {caminho}")
        print("   Recomendação: reinicie o sistema para limpar conexões em cache.")

    except Exception as e:
        logger.exception("Erro ao restaurar backup")
        print(f"❌ Erro ao restaurar: {e}")


# ============================================================
# Menu interativo
# ============================================================


def menu_backup():
    """Sub-menu para o usuário escolher entre criar/listar/restaurar backup."""
    print("\n--- 💾 BACKUP E RESTAURAÇÃO ---")
    print("[1] Fazer backup agora")
    print("[2] Listar backups existentes")
    print("[3] Restaurar um backup")
    print("[0] Voltar")

    opcao = input("\nOpção: ").strip()

    if opcao == "1":
        fazer_backup()
    elif opcao == "2":
        listar_backups()
    elif opcao == "3":
        restaurar_backup()
    elif opcao == "0":
        return
    else:
        print("❌ Opção inválida.")


if __name__ == "__main__":
    menu_backup()
