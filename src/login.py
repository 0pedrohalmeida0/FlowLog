"""Tela de login: fina. Toda lógica de autenticação e lockout
vive em `AuthService`. Aqui só lidamos com I/O do terminal."""

import getpass

from exceptions import AuthenticationError, ContaBloqueadaError, ValidationError
from logging_config import get_logger
from services.auth_service import AuthService

logger = get_logger(__name__)


def fazer_login():
    """Coleta credenciais, chama o service, traduz exceções em mensagens.

    Returns:
        int: nível de acesso (1, 2 ou 3) se autenticado.
        None: se falhar.
    """
    try:
        print("\n🔒 TELA DE LOGIN - FLOWLOG")
        usuario = input("Usuário: ").strip()

        # Atalho para sair do loop de login
        if usuario.upper() == "Q":
            logger.info("Usuário escolheu sair da tela de login")
            return None

        # getpass esconde a senha no terminal; cai em input normal
        # caso o terminal não suporte (alguns terminais antigos no Windows).
        try:
            senha = getpass.getpass("Senha: ")
        except (ImportError, Exception):
            senha = input("Senha: ")

        service = AuthService()
        nivel = service.autenticar(usuario, senha)
        print(f"✅ Login aprovado! Bem-vindo(a), {usuario}. (Nível {nivel})")
        return nivel

    except ContaBloqueadaError as e:
        print(f"⛔ {e}")
        return None
    except AuthenticationError as e:
        print(f"❌ {e}")
        return None
    except ValidationError as e:
        print(f"❌ {e}")
        return None
    except Exception as e:
        # Erro inesperado (DB, etc). Loga com stack trace.
        logger.exception("Erro inesperado durante login")
        print(f"❌ Erro no banco: {e}")
        return None
