import os
from contextlib import contextmanager

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()


class Database:
    """Camada de acesso ao MySQL.

    Oferece duas formas de uso:

    1. Forma legada (single statement, leituras ou escritas pontuais):
        db = Database()
        conn = db.connect()
        if conn:
            cur = conn.cursor()
            cur.execute(...)
            conn.commit()
            cur.close(); conn.close()

    2. Forma recomendada para operações multi-statement (transação atômica):
        with Database().transaction() as (conn, cur):
            cur.execute(...)
            cur.execute(...)
        # commit() automático se nada lançar exceção;
        # rollback() automático se algo falhar;
        # cursor e conexão sempre fechados.
    """

    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME'),
            'auth_plugin': 'mysql_native_password',
        }

    def connect(self):
        """Abre uma conexão simples. Retorna a conexão ou None em caso de erro."""
        try:
            connection = mysql.connector.connect(**self.config, use_pure=True)
            return connection
        except Error as e:
            print(f"❌ Erro ao conectar ao banco: {e}")
            return None

    @contextmanager
    def transaction(self):
        """Context manager que cede (conn, cursor) dentro de uma transação.

        - commit() se o bloco terminar sem exceção;
        - rollback() se o bloco levantar qualquer exceção;
        - cursor e conexão sempre fechados ao final.

        Levanta ConnectionError se não conseguir abrir a conexão.
        """
        conn = self.connect()
        if not conn:
            raise ConnectionError("Não foi possível conectar ao banco de dados FlowLog.")
        cursor = conn.cursor()
        try:
            yield conn, cursor
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            if conn.is_connected():
                conn.close()


if __name__ == "__main__":
    db = Database()
    conn = db.connect()
    if conn:
        print("✅ Sucesso: Conectado ao banco de dados FlowLog!")
        conn.close()
