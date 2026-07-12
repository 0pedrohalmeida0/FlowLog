from database import Database
from utils import verificar_senha


def fazer_login():
    """Autentica o usuário via bcrypt.

    Retorna:
        int: nível de acesso (1, 2 ou 3) se autenticado.
        None: se falhar.
    """
    db = Database()
    conexao = db.connect()

    if not conexao:
        return None

    try:
        print("\n🔒 TELA DE LOGIN - FLOWLOG")
        usuario = input("Usuário: ").strip()

        # Tenta usar getpass pra esconder a senha; cai em input normal
        # caso o terminal não suporte (alguns terminais antigos no Windows).
        try:
            import getpass
            senha = getpass.getpass("Senha: ")
        except (ImportError, Exception):
            senha = input("Senha: ")

        cursor = conexao.cursor()
        cursor.execute(
            "SELECT nivel_acesso, senha FROM usuarios WHERE username = %s",
            (usuario,),
        )
        resultado = cursor.fetchone()
        cursor.close()

        if not resultado:
            print("❌ Usuário ou senha incorretos.")
            return None

        nivel, senha_hash = resultado

        if not verificar_senha(senha, senha_hash):
            print("❌ Usuário ou senha incorretos.")
            return None

        print(f"✅ Login aprovado! Bem-vindo(a), {usuario}. (Nível {nivel})")
        return nivel

    except Exception as e:
        print(f"❌ Erro no banco: {e}")
        return None
    finally:
        if conexao and conexao.is_connected():
            conexao.close()
