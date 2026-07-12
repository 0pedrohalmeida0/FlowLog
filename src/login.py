"""Login com autenticação bcrypt e proteção contra brute-force.

Política de lockout (configurável via .env):
    - LOCKOUT_MAX_ATTEMPTS (padrão 5): tentativas falhas antes do bloqueio.
    - LOCKOUT_DURATION_MINUTES (padrão 15): duração do bloqueio em minutos.

Após o bloqueio, o usuário vê uma mensagem com o tempo restante aproximado.
A contagem de tentativas é zerada em login bem-sucedido e ao iniciar o bloqueio.
"""

import os
from datetime import datetime, timedelta

from database import Database
from logging_config import get_logger
from session import login as session_login
from utils import verificar_senha

logger = get_logger(__name__)


def _get_lockout_config():
    """Lê as configs de lockout do .env (com defaults)."""
    return {
        "max_attempts": int(os.getenv("LOCKOUT_MAX_ATTEMPTS", "5")),
        "duration_minutes": int(os.getenv("LOCKOUT_DURATION_MINUTES", "15")),
    }


def fazer_login():
    """Autentica o usuário via bcrypt, com proteção contra brute-force.

    Retorna:
        int: nível de acesso (1, 2 ou 3) se autenticado.
        None: se falhar (credenciais inválidas, conta bloqueada, etc).

    Efeitos colaterais em caso de sucesso: popula a sessão global via
    `session.login(usuario_id, username, nivel)` e zera o contador de
    tentativas falhas do usuário no banco.
    """
    cfg = _get_lockout_config()
    db = Database()
    conexao = db.connect()
    if not conexao:
        return None

    try:
        print("\n🔒 TELA DE LOGIN - FLOWLOG")
        usuario = input("Usuário: ").strip()

        # Atalho para sair do loop de login
        if usuario.upper() == "Q":
            logger.info("Usuário escolheu sair da tela de login")
            return None

        try:
            import getpass

            senha = getpass.getpass("Senha: ")
        except (ImportError, Exception):
            senha = input("Senha: ")

        cursor = conexao.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, nivel_acesso, senha, tentativas_falhas, bloqueado_ate "
            "FROM usuarios WHERE username = %s",
            (usuario,),
        )
        resultado = cursor.fetchone()
        cursor.close()

        if not resultado:
            # Mesma mensagem de "senha incorreta" para evitar user enumeration.
            logger.warning("Login falhou: usuário '%s' não encontrado", usuario)
            print("❌ Usuário ou senha incorretos.")
            return None

        # Verifica se a conta está bloqueada
        bloqueado_ate = resultado.get("bloqueado_ate")
        if bloqueado_ate and bloqueado_ate > datetime.now():
            restante_min = (bloqueado_ate - datetime.now()).total_seconds() / 60
            restante_int = int(restante_min) + 1
            logger.warning(
                "Login bloqueado para '%s' (desbloqueia em ~%d min)",
                usuario,
                restante_int,
            )
            print(
                f"⛔ Conta bloqueada por excesso de tentativas. "
                f"Tente novamente em ~{restante_int} min."
            )
            return None

        # Verifica a senha
        if not verificar_senha(senha, resultado["senha"]):
            return _registrar_falha_login(
                conexao,
                resultado["id"],
                usuario,
                cfg,
            )

        # Sucesso: zera tentativas, marca desbloqueio, abre sessão
        update_cursor = conexao.cursor()
        update_cursor.execute(
            "UPDATE usuarios SET tentativas_falhas = 0, bloqueado_ate = NULL " "WHERE id = %s",
            (resultado["id"],),
        )
        conexao.commit()
        update_cursor.close()

        session_login(resultado["id"], usuario, resultado["nivel_acesso"])
        logger.info(
            "Login OK: usuário='%s' id=%d nível=%d",
            usuario,
            resultado["id"],
            resultado["nivel_acesso"],
        )
        print(f"✅ Login aprovado! Bem-vindo(a), {usuario}. (Nível {resultado['nivel_acesso']})")
        return resultado["nivel_acesso"]

    except Exception as e:
        logger.exception("Erro inesperado durante login")
        print(f"❌ Erro no banco: {e}")
        return None
    finally:
        if conexao and conexao.is_connected():
            conexao.close()


def _registrar_falha_login(conexao, usuario_id, usuario, cfg):
    """Incrementa o contador de tentativas falhas; bloqueia se atingir o limite.

    Retorna sempre None (login falhou).
    """
    max_attempts = cfg["max_attempts"]
    duration = cfg["duration_minutes"]

    # Lê o contador atual e decide se bloqueia
    cur = conexao.cursor(dictionary=True)
    cur.execute(
        "SELECT tentativas_falhas FROM usuarios WHERE id = %s",
        (usuario_id,),
    )
    row = cur.fetchone()
    cur.close()

    tentativas = (row["tentativas_falhas"] if row else 0) + 1

    update_cur = conexao.cursor()
    try:
        if tentativas >= max_attempts:
            bloqueado_ate = datetime.now() + timedelta(minutes=duration)
            update_cur.execute(
                "UPDATE usuarios SET tentativas_falhas = 0, bloqueado_ate = %s " "WHERE id = %s",
                (bloqueado_ate, usuario_id),
            )
            conexao.commit()
            logger.warning(
                "Conta '%s' BLOQUEADA após %d tentativas falhas (duração: %d min)",
                usuario,
                tentativas,
                duration,
            )
            print(f"⛔ Conta bloqueada por {duration} min após " f"{tentativas} tentativas falhas.")
        else:
            update_cur.execute(
                "UPDATE usuarios SET tentativas_falhas = %s WHERE id = %s",
                (tentativas, usuario_id),
            )
            conexao.commit()
            restantes = max_attempts - tentativas
            logger.warning(
                "Senha incorreta para '%s' (%d/%d)",
                usuario,
                tentativas,
                max_attempts,
            )
            print(
                f"❌ Senha incorreta. {restantes} tentativa(s) " f"restante(s) antes do bloqueio."
            )
    finally:
        update_cur.close()

    return None
