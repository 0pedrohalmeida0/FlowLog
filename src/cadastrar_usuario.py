from database import Database
from logging_config import get_logger
from utils import hash_senha, validar_senha_complexidade


logger = get_logger(__name__)


def cadastrar_usuario():
    print("\n--- 🛡️ CADASTRO DE NOVOS USUÁRIOS (ACESSO RESTRITO) ---")

    novo_username = input("Digite o nome do novo usuário: ").strip()
    if not novo_username:
        print("❌ Erro: nome de usuário não pode ser vazio.")
        return

    # Loop até o usuário fornecer uma senha que passa na validação
    while True:
        nova_senha = input("Digite a senha de acesso: ")
        ok, msg = validar_senha_complexidade(nova_senha)
        if ok:
            break
        print(f"❌ {msg}")

    try:
        nivel = int(input("Nível de acesso (1 - Operador | 2 - Gerente | 3 - Admin): ").strip())
    except ValueError:
        print("❌ Erro: digite apenas números para o nível de acesso.")
        return

    if nivel not in (1, 2, 3):
        print("❌ Erro: nível deve ser 1, 2 ou 3.")
        return

    # Hash bcrypt (60 chars em utf-8; coluna senha precisa de VARCHAR(60) ou mais)
    senha_hash = hash_senha(nova_senha).decode('utf-8')

    db = Database()
    conexao = db.connect()
    if not conexao:
        return

    try:
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO usuarios (username, senha, nivel_acesso) VALUES (%s, %s, %s)",
            (novo_username, senha_hash, nivel),
        )
        conexao.commit()
        logger.info("Usuário '%s' cadastrado com nível %d", novo_username, nivel)
        print(f"\n✅ Sucesso! O usuário '{novo_username}' foi cadastrado com Nível {nivel}.")
    except Exception as e:
        try:
            conexao.rollback()
        except Exception:
            pass
        erro = str(e).lower()
        if 'duplicate' in erro or 'unique' in erro:
            logger.warning("Tentativa de cadastrar username duplicado: '%s'", novo_username)
            print(f"\n❌ Falha: o usuário '{novo_username}' já existe.")
        else:
            logger.exception("Falha ao cadastrar usuário '%s'", novo_username)
            print(f"\n❌ Falha ao cadastrar: {e}")
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        if conexao and conexao.is_connected():
            conexao.close()


if __name__ == "__main__":
    cadastrar_usuario()
