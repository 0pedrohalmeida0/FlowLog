import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv  

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class Database:
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME'),
            'auth_plugin': 'mysql_native_password'
}

    def connect(self):
        try:
            connection = mysql.connector.connect(**self.config, use_pure=True)
            if connection.is_connected():
                print("✅ Sucesso: Conectado ao banco de dados FlowLog!")
                return connection
        except Error as e:
            print(f"❌ Erro ao conectar: {e}")
            return None

if __name__ == "__main__":
        db = Database()
        db.connect()