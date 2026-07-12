"""Configuração central de logging do FlowLog.

Por que logging e não print:
- Níveis (DEBUG/INFO/WARNING/ERROR) para filtrar o que importa.
- Timestamps consistentes (úteis em auditoria / suporte).
- Saída em arquivo rotativo (10 MB x 5 backups) sem intervenção manual.
- Formato estruturado que pode ser parseado por ferramentas externas.

Chamada típica: uma vez no startup do main.py, antes de tudo.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

_CONSOLE_FORMAT = "[%(asctime)s] [%(levelname)s] %(message)s"
_FILE_FORMAT = "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"
_DATE_FORMAT = "%H:%M:%S"
_FILE_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Diretório de logs: <raiz do projeto>/logs/flowlog.log
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOG_DIR = os.path.join(_PROJECT_ROOT, "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "flowlog.log")


def setup_logging(level=logging.INFO, log_to_file=True, max_bytes=10 * 1024 * 1024, backups=5):
    """Configura logging com saída no console e (opcionalmente) em arquivo rotativo.

    Idempotente: chamadas múltiplas não duplicam handlers (usado por testes
    e reentradas).

    Args:
        level: nível mínimo para o console (INFO por padrão).
        log_to_file: se True, adiciona RotatingFileHandler.
        max_bytes: tamanho máximo do arquivo de log antes de rotacionar.
        backups: quantidade de arquivos antigos mantidos.
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # captura tudo; cada handler filtra depois

    if root.handlers:
        return  # já configurado, não duplica

    # Console: nível controlado por `level`, formato curto e legível
    console_formatter = logging.Formatter(_CONSOLE_FORMAT, _DATE_FORMAT)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    root.addHandler(console_handler)

    if log_to_file:
        try:
            os.makedirs(_LOG_DIR, exist_ok=True)
            file_formatter = logging.Formatter(_FILE_FORMAT, _FILE_DATE_FORMAT)
            file_handler = RotatingFileHandler(
                _LOG_FILE,
                maxBytes=max_bytes,
                backupCount=backups,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)  # arquivo captura tudo
            file_handler.setFormatter(file_formatter)
            root.addHandler(file_handler)
        except OSError as e:
            # Sem permissão pra escrever no disco? Segue só com console.
            root.warning("Não foi possível criar arquivo de log em %s: %s", _LOG_FILE, e)


def get_logger(name):
    """Helper para obter um logger nomeado.

    Uso:
        from logging_config import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)
