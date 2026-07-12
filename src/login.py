from database import Database
from logging_config import get_logger
from session import login as session_login
from utils import verificar_senha


logger = get_logger(__name__)


def fazer_login():
    """Autentica o usuário via bcrypt e popula a sessão.

    Retorna:
        int: nível de acesso (1, 2 ou 3) se autenticado.
        None: se falhar.

    Efeitos colaterais em caso de sucesso: popula a sessão global via
    `session.login(usuario_id, username, nivel)`, permitindo que outros
    módulos (entrada, saida, relatorios) saibam quem está logado.
    """
    db = Database()
    conexao = db.connect()

    if not conexao:
        return None

    try:
        print("\n🔒 TELA DE LOGIN - FLOWLOG")
        usuario = input("Usuário: ").strip()

        # getpass esconde a senha no terminal; cai em input normal
        # caso o terminal não suporte (alguns terminais antigos no Windows).
        try:
            import getpass
            senha = getpass.getpass("Senha: ")
        except (ImportError, Exception):
            senha = input("Senha: ")

        cursor = conexao.cursor()
        cursor.execute(
            "SELECT id, nivel_acesso, senha FROM usuarios WHERE username = %s",
            (usuario,),
        )
        resultado = cursor.fetchone()
        cursor.close()

        if not resultado:
            logger.warning("Login falhou: usuário '%s' não encontrado", usuario)
            print("❌ Usuário ou senha incorretos.")
            return None

        usuario_id, nivel, senha_hash = resultado

        if not verificar_senha(senha, senha_hash):
            logger.warning("Login falhou: senha incorreta para '%s'", usuario)
            print("❌ Usuário ou senha incorretos.")
            return None

        # Sucesso: popula a sessão e loga
        session_login(usuario_id, usuario, nivel)
        logger.info("Login OK: usuário='%s' id=%d nível=%d", usuario, usuario_id, nivel)
        print(f"✅ Login aprovado! Bem-vindo(a), {usuario}. (Nível {nivel})")
        return nivel

    except Exception as e:
        logger.exception("Erro inesperado durante login")
        print(f"❌ Erro no banco: {e}")
        return None
    finally:
        if conexao and conexao.is_connected():
            conexao.close()
