from database import Database

def cadastrar_produto_teste():
    db = Database()
    conexao = db.connect()
    
    if conexao:
        try:
            cursor = conexao.cursor()
            
            # Dados do produto que vamos inserir
            nome = "Item de Teste Logístico"
            qtd = 50
            preco = 15.90
            
            sql = "INSERT INTO produtos (nome, quantidade, preco_custo) VALUES (%s, %s, %s)"
            valores = (nome, qtd, preco)
            
            cursor.execute(sql, valores)
            conexao.commit() # IMPORTANTE: Salva a alteração no banco
            
            print(f"✅ {cursor.rowcount} produto cadastrado com sucesso!")
            
            cursor.close()
            conexao.close()
        except Exception as e:
            print(f"❌ Erro ao inserir: {e}")

if __name__ == "__main__":
    cadastrar_produto_teste()