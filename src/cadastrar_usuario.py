from database import Database
from utils import hash_senha


def cadastrar_usuario():
    print("\n--- 🛡️ CADASTRO DE NOVOS USUÁRIOS (ACESSO RESTRITO) ---")

    novo_username = input("Digite o nome do novo usuário: ").strip()
    if not novo_username:
        print("❌ Erro: nome de usuário não pode ser vazio.")
        return

    nova_senha = input("Digite a senha de acesso: ")
    if len(nova_senha) < 6:
        print("❌ Erro: a senha deve ter no mínimo 6 caracteres.")
        return

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
        sql = (
            "INSERT INTO usuarios (username, senha, nivel_acesso) "
            "VALUES (%s, %s, %s)"
        )
        cursor.execute(sql, (novo_username, senha_hash, nivel))
        conexao.commit()
        print(
            f"\n✅ Sucesso! O usuário '{novo_username}' foi cadastrado com Nível {nivel}."
        )
    except Exception as e:
        try:
            conexao.rollback()
        except Exception:
            pass
        erro = str(e).lower()
        if 'duplicate' in erro or 'unique' in erro:
            print(f"\n❌ Falha: o usuário '{novo_username}' já existe.")
        else:
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
