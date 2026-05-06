from database import Database

def listar_todos_produtos():
    db = Database()
    conexao = db.connect()
    
    if conexao:
        try:
            cursor = conexao.cursor()
            sql = "SELECT id, nome, quantidade, preco_custo, data_entrada FROM produtos"
            cursor.execute(sql)
            resultados = cursor.fetchall()
            
            print("\n--- RELATÓRIO DE INVENTÁRIO (FLOWLOG) ---")
            print(f"{'ID':<4} | {'NOME':<25} | {'QTD':<5} | {'PREÇO':<10}")
            print("-" * 50)
            
            for produto in resultados:
                id_p, nome, qtd, preco, data = produto
                print(f"{id_p:<4} | {nome:<25} | {qtd:<5} | R$ {preco:<10.2f}")
            
            print("-" * 50)
            
            cursor.close()
            conexao.close()
        except Exception as e:
            print(f"❌ Erro ao listar produtos: {e}")

# A função precisa estar aqui, fora do bloco 'if __name__'
def alerta_estoque_baixo():
    db = Database()
    conexao = db.connect()
    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute("SELECT nome, quantidade FROM produtos WHERE quantidade < 5")
            criticos = cursor.fetchall()
            
            if criticos:
                print("\n" + "!" * 40)
                print("⚠️  ATENÇÃO: ITENS COM ESTOQUE BAIXO!")
                for nome, qtd in criticos:
                    print(f" - {nome}: apenas {qtd} unidades!")
                print("!" * 40)
            
            cursor.close()
            conexao.close()
        except Exception as e:
            print(f"Erro ao verificar alertas: {e}")

# Este bloco fica SEMPRE no final do arquivo
if __name__ == "__main__":
    listar_todos_produtos() 
    alerta_estoque_baixo()