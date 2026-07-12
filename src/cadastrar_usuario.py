"""Tela fina de cadastro de usuário. Lógica em `UsuarioService`."""

from mysql.connector import IntegrityError

from exceptions import ValidationError
from logging_config import get_logger
from services.usuario_service import UsuarioService

logger = get_logger(__name__)


def cadastrar_usuario():
    print("\n--- 🛡️ CADASTRO DE NOVOS USUÁRIOS (ACESSO RESTRITO) ---")

    novo_username = input("Digite o nome do novo usuário: ").strip()

    # Loop até o usuário fornecer uma senha que passa na validação
    while True:
        # ME-13: strip() na senha evita criação de senhas com whitespace
        # acidental (ex: ' abc123 '). A validação de complexidade roda
        # dentro do service, mas a normalização fica aqui.
        nova_senha = input("Digite a senha de acesso: ").strip()
        if not nova_senha:
            print("❌ A senha não pode ser vazia.")
            continue
        break  # o service levanta ValidationError com a mensagem

    try:
        nivel = int(input("Nível de acesso (1 - Operador | 2 - Gerente | 3 - Admin): ").strip())
    except ValueError:
        print("❌ Erro: digite apenas números para o nível de acesso.")
        return

    # AL-04: delega tudo para UsuarioService.cadastrar()
    service = UsuarioService()
    try:
        service.cadastrar(novo_username, nova_senha, nivel)
    except ValidationError as e:
        print(f"\n❌ {e}")
        return
    except IntegrityError as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            logger.warning("Tentativa de cadastrar username duplicado: '%s'", novo_username)
            print(f"\n❌ Falha: o usuário '{novo_username}' já existe.")
        else:
            logger.exception("Falha ao cadastrar usuário '%s'", novo_username)
            print(f"\n❌ Falha ao cadastrar: {e}")
        return
    except Exception as e:
        logger.exception("Falha inesperada ao cadastrar usuário '%s'", novo_username)
        print(f"\n❌ Falha inesperada: {e}")
        return

    print(f"\n✅ Sucesso! O usuário '{novo_username}' foi cadastrado com Nível {nivel}.")


if __name__ == "__main__":
    cadastrar_usuario()
