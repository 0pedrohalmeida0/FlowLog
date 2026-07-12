"""Camada de acesso ao MySQL com pool de conexões.

O pool (MySQLConnectionPool) é compartilhado entre todas as instâncias de
Database — é um singleton por classe, criado lazy na primeira chamada.
Cada conexão retornada por `connect()` vem do pool; `close()` a devolve
para reuso. Em escala, isso evita o overhead de abrir/fechar socket TCP
a cada operação.
"""

import os
from contextlib import contextmanager

from dotenv import load_dotenv
from mysql.connector import Error, pooling

from logging_config import get_logger

load_dotenv()

logger = get_logger(__name__)


class Database:
    """Acesso ao MySQL com pool de conexões singleton.

    Oferece duas formas de uso:

    1. Forma legada (single statement, leituras ou escritas pontuais):
        db = Database()
        conn = db.connect()
        if conn:
            cur = conn.cursor()
            cur.execute(...)
            conn.commit()
            cur.close(); conn.close()  # devolve ao pool

    2. Forma recomendada para operações multi-statement (transação atômica):
        with Database().transaction() as (conn, cur):
            cur.execute(...)
            cur.execute(...)
        # commit() automático se nada lançar exceção;
        # rollback() automático se algo falhar;
        # cursor e conexão sempre fechados (close devolve ao pool).
    """

    _pool = None  # singleton: compartilhado entre instâncias

    def __init__(self):
        # Não cria o pool aqui — só quando alguém pedir.
        # Isso facilita testes e evita falha cedo se o .env não estiver pronto.
        pass

    @classmethod
    def _get_config(cls):
        return {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
            "auth_plugin": "mysql_native_password",
        }

    @classmethod
    def _get_pool(cls, pool_size=5):
        if cls._pool is None:
            try:
                cls._pool = pooling.MySQLConnectionPool(
                    pool_name="flowlog_pool",
                    pool_size=pool_size,
                    **cls._get_config(),
                )
                logger.info("Pool MySQL inicializado (pool_size=%d)", pool_size)
            except Error as e:
                logger.error("Falha ao criar pool MySQL: %s", e)
                raise
        return cls._pool

    def connect(self):
        """Pega uma conexão do pool. Retorna None se o pool não puder fornecer."""
        try:
            return self._get_pool().get_connection()
        except Error as e:
            # CR-06: sanitiza mensagens de erro do MySQL antes de logar.
            # O driver às vezes ecoa parâmetros (incluindo senha) nas
            # exceções. Nunca logamos o erro bruto.
            safe = self._sanitize_error(e)
            logger.error("Erro ao obter conexão do pool: %s", safe)
            return None

    @staticmethod
    def _sanitize_error(err: Exception) -> str:
        """CR-06: remove qualquer parâmetro sensível de mensagens do MySQL.

        Substitui padrões comuns: password=***, user=***, host=***.
        O driver MySQL Connector/Python em geral não vaza a senha, mas
        outras exceções (ex.: `pool_name=flowlog_pool`) também não
        precisam aparecer. Defesa em profundidade.
        """
        import re

        msg = str(err)
        msg = re.sub(
            r"password\s*=\s*['\"]?[^'\"\s)]+",
            "password=***",
            msg,
            flags=re.IGNORECASE,
        )
        msg = re.sub(
            r"(?P<key>user|host|port|host_name)\s*=\s*['\"]?[^'\"\s)]+",
            r"\g<key>=***",
            msg,
            flags=re.IGNORECASE,
        )
        return msg

    @contextmanager
    def transaction(self):
        """Context manager que cede (conn, cursor) dentro de uma transação.

        - commit() se o bloco terminar sem exceção;
        - rollback() se o bloco levantar qualquer exceção;
        - cursor.close() e conn.close() sempre (close devolve ao pool).

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
            try:
                conn.close()  # devolve ao pool, não fecha a conexão real
            except Exception:
                pass


if __name__ == "__main__":
    db = Database()
    conn = db.connect()
    if conn:
        logger.info("Sucesso: conectado ao banco de dados FlowLog!")
        conn.close()
    else:
        logger.error("Não foi possível conectar ao banco.")
