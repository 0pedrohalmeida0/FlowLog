"""Entry point principal do FlowLog.

Quando o usuário instala via `pip install flowlog` ou roda o executável
empacotado (PyInstaller), este é o módulo chamado.

Fluxo:
    1. Parse args (--setup, --version, --check-update)
    2. Setup wizard se necessário (primeiro start ou --setup)
    3. Checa atualização (se --check-update)
    4. Inicia o app CLI (src.main:menu)
"""

import argparse
import sys

from logging_config import get_logger, setup_logging

__version__ = "1.5.0"
logger = get_logger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="flowlog",
        description="FlowLog — sistema de gestão de inventário",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"FlowLog {__version__}",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Força o setup wizard (mesmo se já configurado)",
    )
    parser.add_argument(
        "--check-update",
        action="store_true",
        help="Verifica se há atualização disponível",
    )
    parser.add_argument(
        "--ativar",
        metavar="CHAVE",
        help="Ativa uma chave de licença e sai",
    )

    args = parser.parse_args()

    # Setup logging cedo (silencioso durante wizard, INFO depois)
    setup_logging()

    # Comando: ativar chave
    if args.ativar:
        from licenca import ativar_licenca

        try:
            novo = ativar_licenca(args.ativar)
            print(f"✅ Licença ativada! ID: {novo.cliente_hash[:12]}...")
            print(f"   Modo: {novo.modo}")
            if novo.expira_em:
                print(f"   Expira em: {novo.expira_em.date()}")
            return 0
        except ValueError as e:
            print(f"❌ {e}")
            return 1

    # Comando: check update
    if args.check_update:
        from auto_update import checar_atualizacao

        info = checar_atualizacao(__version__)
        if info is None:
            print("✅ Você está na versão mais recente.")
            return 0
        print(f"🆕 Nova versão disponível: {info['version']}")
        print(f"   {info['url']}")
        print(f"   Notas: {info['notes']}")
        return 0

    # Setup wizard (se necessário)
    from setup_wizard import wizard_se_necessario

    if not wizard_se_necessario(forcar=args.setup):
        return 1

    # Checagem de atualização não-bloqueante
    try:
        from auto_update import checar_atualizacao_background

        checar_atualizacao_background(__version__)
    except Exception as e:
        logger.debug("Falha ao checar update: %s", e)

    # Inicia o app principal
    from main import menu

    try:
        menu()
        return 0
    except KeyboardInterrupt:
        print("\n\n👋 Até logo!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
