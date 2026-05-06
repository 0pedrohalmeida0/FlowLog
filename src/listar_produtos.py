from database import Database

def listar_todos_produtos():
    db = Database()
    conexao = db.connect()
    
    if conexao:
        try:
            cursor = conexao.cursor()
            
            # Comando SQL para buscar tudo da tabela produtos
            sql = "SELECT id, nome, quantidade, preco_custo, data_entrada FROM produtos"
            cursor.execute(sql)
            
            # O fetchall() pega todas as linhas que o banco encontrou
            resultados = cursor.fetchall()
            
            print("\n--- RELATÓRIO DE INVENTÁRIO (FLOWLOG) ---")
            print(f"{'ID':<4} | {'NOME':<25} | {'QTD':<5} | {'PREÇO':<10}")
            print("-" * 50)
            
            for produto in resultados:
                id_p, nome, qtd, preco, data = produto
                # Formatando a exibição para ficar alinhada
                print(f"{id_p:<4} | {nome:<25} | {qtd:<5} | R$ {preco:<10.2f}")
            
            print("-" * 50)
            
            cursor.close()
            conexao.close()
        except Exception as e:
            print(f"❌ Erro ao listar produtos: {e}")

if __name__ == "__main__":
    listar_todos_produtos() 