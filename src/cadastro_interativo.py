from database import Database

def cadastrar_produto_interativo():
    db = Database()
    conexao = db.connect()
    
    if conexao:
        try:
            print("\n--- CADASTRO DE PRODUTO FLOWLOG ---")
            
            # Coletando os dados do usuário
            nome = input("Digite o nome do produto: ")
            quantidade = int(input("Digite a quantidade em estoque: "))
            preco = float(input("Digite o preço de custo (ex: 10.50): "))
            
            cursor = conexao.cursor()
            
            sql = "INSERT INTO produtos (nome, quantidade, preco_custo) VALUES (%s, %s, %s)"
            valores = (nome, quantidade, preco)
            
            cursor.execute(sql, valores)
            conexao.commit()
            
            print(f"\n✅ Sucesso! '{nome}' foi adicionado ao inventário.")
            
            cursor.close()
            conexao.close()
            
        except ValueError:
            print("❌ Erro: No campo quantidade e preço, use apenas números.")
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    cadastrar_produto_interativo()