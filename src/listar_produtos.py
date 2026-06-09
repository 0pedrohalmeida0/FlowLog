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
            
            # O NOVO COMANDO SQL INTELIGENTE
            sql = "SELECT nome, quantidade, alerta_minimo FROM produtos WHERE alerta_minimo IS NOT NULL AND quantidade <= alerta_minimo"
            cursor.execute(sql)
            produtos_baixos = cursor.fetchall()
            
            if produtos_baixos:
                print("\n" + "!"*40)
                print(" 🚨 ALERTA DE ESTOQUE CRÍTICO 🚨")
                print("!"*40)
                for produto in produtos_baixos:
                    # produto[0] = nome | produto[1] = quantidade | produto[2] = alerta_minimo
                    print(f"⚠️ {produto[0]}: Restam apenas {produto[1]} unidades! (Mínimo: {produto[2]})")
                print("!"*40 + "\n")
                
            cursor.close()
            conexao.close()
            
        except Exception as e:
            print(f"Erro ao verificar alertas de estoque: {e}")

# Este bloco fica SEMPRE no final do arquivo
if __name__ == "__main__":
    listar_todos_produtos() 
    alerta_estoque_baixo()