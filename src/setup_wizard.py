"""Setup wizard do FlowLog Licença.

Roda no primeiro start (ou quando .env não existe / wizard_force=1).
Passos:
    1. Saudação + aceite de EULA
    2. Configurar conexão MySQL (host, porta, user, senha, nome do banco)
    3. Testar conexão
    4. Rodar schema.sql (criar tabelas)
    5. Criar admin user padrão (admin / admin123, força troca)
    6. Iniciar trial de 30 dias
    7. Imprimir próximos passos

Idempotente: se o wizard já rodou, ele pode ser chamado de novo e
detecta que já está configurado (pula direto pra login).
"""

import os
import re
import sys
from pathlib import Path

from licenca import inicializar_trial
from logging_config import get_logger
from utils import hash_senha

logger = get_logger(__name__)


PROJECT_ROOT = Path(__file__).parent.parent  # /workspace/FlowLog
SCHEMA_PATH = PROJECT_ROOT / "schema.sql"
ENV_PATH = PROJECT_ROOT / ".env"
ENV_EXAMPLE_PATH = PROJECT_ROOT / ".env.example"


# ============================================================
# Helpers de I/O
# ============================================================


def _env_path() -> Path:
    """Permite override via FLOWLOG_HOME (usado no instalador Windows)."""
    custom = os.environ.get("FLOWLOG_HOME")
    if custom:
        return Path(custom) / ".env"
    return ENV_PATH


def _mysql_config_existe() -> bool:
    """Detecta se o .env tem as 4 vars obrigatórias."""
    path = _env_path()
    if not path.exists():
        return False
    txt = path.read_text(encoding="utf-8")
    required = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]
    return all(re.search(rf"^{k}=.+$", txt, re.MULTILINE) for k in required)


def _admin_user_existe() -> bool:
    """Tenta contar usuários no banco. True se >= 1."""
    try:
        from database import Database

        db = Database()
        conn = db.connect()
        if not conn:
            return False
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM usuarios")
            n = cur.fetchone()[0]
            return n > 0
        finally:
            try:
                cur.close()
            except Exception:
                pass
            if conn.is_connected():
                conn.close()
    except Exception as e:
        logger.debug("Falha ao checar admin: %s", e)
        return False


def _rodar_schema_sql(conn) -> bool:
    """Executa schema.sql no banco. Retorna True se OK."""
    if not SCHEMA_PATH.exists():
        print(f"❌ Erro: schema.sql não encontrado em {SCHEMA_PATH}")
        return False
    try:
        sql_text = SCHEMA_PATH.read_text(encoding="utf-8")
        cur = conn.cursor()
        # MySQL não aceita múltiplos statements com execute() simples
        # sem opção multi=True. Pra garantir compatibilidade, separamos
        # por ';' e rodamos um por um.
        statements = [s.strip() for s in sql_text.split(";") if s.strip()]
        for stmt in statements:
            cur.execute(stmt)
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao rodar schema.sql: {e}")
        logger.exception("Erro no schema")
        return False


def _criar_admin_user(conn, username: str, senha: str) -> bool:
    """Cria o admin user com nível 3 (Admin TI)."""
    try:
        senha_hash = hash_senha(senha).decode("utf-8")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO usuarios (username, senha, nivel_acesso) VALUES (%s, %s, %s)",
            (username, senha_hash, 3),
        )
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao criar admin: {e}")
        return False


def _escrever_env(config: dict) -> None:
    """Escreve o .env com a config do MySQL."""
    path = _env_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    # Se já existe .env.example, usa como base (preserva comentários)
    if ENV_EXAMPLE_PATH.exists() and not path.exists():
        base = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    else:
        base = "# FlowLog .env\n"

    # Aplica/sobrescreve as 4 vars
    lines = base.splitlines()
    vars_to_set = {
        "DB_HOST": config["host"],
        "DB_USER": config["user"],
        "DB_PASSWORD": config["password"],
        "DB_NAME": config["name"],
    }

    new_lines = []
    seen = set()
    for line in lines:
        match = re.match(r"^([A-Z_]+)=", line)
        if match and match.group(1) in vars_to_set:
            key = match.group(1)
            new_lines.append(f"{key}={vars_to_set[key]}")
            seen.add(key)
        else:
            new_lines.append(line)

    # Adiciona vars que não estavam no .env.example
    for key, value in vars_to_set.items():
        if key not in seen:
            new_lines.append(f"{key}={value}")

    # Permissão 0o600 (defesa em profundidade — senha em plaintext aqui)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines) + "\n")
    except Exception:
        os.close(fd)
        raise

    print(f"✅ Configuração salva em {path}")


# ============================================================
# Passos do wizard
# ============================================================


def _wizard_aceitar_eula() -> bool:
    print("=" * 70)
    print(" 🛡️  FLOWLOG — ACORDO DE LICENÇA DE USUÁRIO FINAL (EULA)")
    print("=" * 70)
    print("""
O FlowLog Licença é um software proprietário. Ao usar este software,
você concorda com:

  1. **Trial**: 30 dias de uso gratuito com todas as features. Após o
     trial, é necessário ativar com uma chave de licença.

  2. **Licença**: comprada uma vez (vitalícia) ou anualmente. Uma chave
     por instalação.

  3. **Restrições**: não é permitido redistribuir o software sem
     autorização. Não é permitido fazer engenharia reversa do esquema
     de licenciamento.

  4. **Suporte**: incluído durante o período da licença. Veja
     https://flowlog.app/suporte para canais oficiais.

  5. **Garantia**: o software é fornecido "como está", sem garantias
     expressas. O backup regular é responsabilidade do usuário.

Para a EULA completa, veja LICENSE.md no diretório de instalação.
""")
    resp = input("Aceita os termos? (S/N): ").strip().upper()
    if resp != "S":
        print("\n❌ EULA não aceita. Setup cancelado.")
        return False
    return True


def _wizard_config_mysql() -> dict | None:
    print("\n--- ⚙️ CONFIGURAÇÃO DO MySQL ---")
    print("Você precisa de um MySQL rodando. Se não tem, instale:")
    print("  • Windows: https://dev.mysql.com/downloads/installer/")
    print("  • Linux:   sudo apt install mysql-server")
    print("  • macOS:   brew install mysql")
    print()

    host = input("Host do MySQL [localhost]: ").strip() or "localhost"
    porta = input("Porta [3306]: ").strip() or "3306"
    user = input("Usuário MySQL [root]: ").strip() or "root"
    password = input("Senha do MySQL: ")
    name = input("Nome do banco [flowlog]: ").strip() or "flowlog"

    return {
        "host": host,
        "port": porta,
        "user": user,
        "password": password,
        "name": name,
    }


def _wizard_testar_conexao(config: dict) -> bool:
    """Tenta conectar e criar o database se não existir."""
    try:
        # Primeiro, conecta SEM especificar database (pra criar)
        # Não tem como via Database() — usa mysql-connector direto
        import mysql.connector

        from database import Database

        conn = mysql.connector.connect(
            host=config["host"],
            port=int(config["port"]),
            user=config["user"],
            password=config["password"],
        )
        cur = conn.cursor()
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{config['name']}` "
            "DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        cur.close()
        conn.close()

        # Agora conecta no database específico
        db = Database()
        conn = db.connect()
        if not conn:
            return False
        print("✅ Conexão com MySQL OK!")
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        print("   Verifique host, porta, user e senha.")
        return False


def _wizard_rodar_schema() -> bool:
    print("\n--- 🗂️ CRIANDO TABELAS ---")
    try:
        from database import Database

        db = Database()
        conn = db.connect()
        if not conn:
            return False
        try:
            ok = _rodar_schema_sql(conn)
            if ok:
                print("✅ Tabelas criadas (ou já existiam)")
            return ok
        finally:
            if conn and conn.is_connected():
                conn.close()
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def _wizard_criar_admin() -> bool:
    print("\n--- 👤 CRIAR ADMIN USER ---")
    username = input("Nome do admin [admin]: ").strip() or "admin"
    print("Senha do admin (mínimo 6 chars, com letra E número):")
    while True:
        senha = input("Senha: ")
        from utils import validar_senha_complexidade

        ok, msg = validar_senha_complexidade(senha)
        if ok:
            break
        print(f"❌ {msg}")

    confirma = input("Tem certeza? Digite 'CRIAR' para confirmar: ").strip()
    if confirma != "CRIAR":
        print("❌ Cancelado")
        return False

    try:
        from database import Database

        db = Database()
        conn = db.connect()
        if not conn:
            return False
        try:
            ok = _criar_admin_user(conn, username, senha)
            if ok:
                print(f"✅ Admin '{username}' criado (nível 3 — Admin TI)")
                print("   ⚠️  Recomendação: troque a senha após o primeiro login.")
            return ok
        finally:
            if conn and conn.is_connected():
                conn.close()
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


# ============================================================
# Entry point
# ============================================================


def wizard_forcado() -> bool:
    """Força o wizard (usado por --setup ou primeiro start)."""
    print("\n🛠️  FLOWLOG SETUP WIZARD\n")
    if not _wizard_aceitar_eula():
        return False

    config = _wizard_config_mysql()
    if config is None:
        return False
    if not _wizard_testar_conexao(config):
        return False
    _escrever_env(config)

    if not _wizard_rodar_schema():
        return False
    if not _wizard_criar_admin():
        return False

    # Inicia trial
    estado = inicializar_trial()
    print(f"\n🎉 Setup concluído! Trial de {estado.dias_restantes_trial()} dias iniciado.")
    print("\nPróximos passos:")
    print("  1. Execute o FlowLog: `flowlog`")
    print("  2. Faça login com o admin criado")
    print("  3. Cadastre produtos e fornecedores")
    print("  4. Em `docs/venda/UPGRADE.md`, veja como ativar a licença completa")
    return True


def wizard_se_necessario(forcar: bool = False) -> bool:
    """Detecta se precisa rodar o wizard. Se sim, roda.

    Returns:
        True se está tudo configurado (wizard rodou ou não era necessário).
        False se o usuário cancelou.
    """
    if forcar:
        return wizard_forcado()

    if _mysql_config_existe() and _admin_user_existe():
        # Tudo pronto — sem wizard
        # Garante que tem um estado de licença (trial ou activated)
        inicializar_trial()
        return True

    print(
        "\n👋 Bem-vindo ao FlowLog! É a primeira vez que você roda.\n"
        "Vamos configurar em 5 passos rápidos.\n"
    )
    return wizard_forcado()


if __name__ == "__main__":
    success = wizard_forcado()
    sys.exit(0 if success else 1)
