from database import Database
from utils import normalize_cnpj

def cadastrar_produto_interativo():
    db = Database()
    conexao = db.connect()
    
    if conexao:
        try:
            print("\n--- CADASTRO DE PRODUTO FLOWLOG ---")
            
            # Coletando os dados principais
            nome = input("Digite o nome do produto: ")
            quantidade = int(input("Digite a quantidade em estoque: "))
            preco = float(input("Digite o preço de custo (ex: 10.50): "))
            
            
            alerta_minimo = None
            while True:
                resposta_alerta = input("Deseja configurar um alerta de estoque mínimo para este produto? (S/N): ").strip().upper()
                if resposta_alerta == "S":
                    alerta_minimo = int(input("Digite a quantidade mínima para alerta: "))
                    break
                elif resposta_alerta == "N":
                    break
                else:
                    print("Resposta inválida. Digite apenas 'S' ou 'N'.")
                    
                db = Database()
                conexao = db.connect()

            # Coletando o CNPJ para iniciar a lógica do fornecedor
            cnpj_fornecedor = normalize_cnpj(input("Digite o CNPJ do fornecedor: "))
            
            cursor = conexao.cursor()
            
            # 1. Faz uma busca (SELECT) no banco para ver se o CNPJ já existe
            sql_busca_fornecedor = (
                "SELECT id FROM fornecedores "
                "WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), ' ', '') = %s"
            )
            cursor.execute(sql_busca_fornecedor, (cnpj_fornecedor,))
            resultado = cursor.fetchone() 
            
            if resultado:
                # O fetchone retorna uma tupla, ex: (1,)
                fornecedor_id = resultado[0]
                print(f"👉 Fornecedor já cadastrado encontrado (ID: {fornecedor_id}).")
            else:
                # O fornecedor não existe no banco, então cadastrá-lo agora
                print("\nℹ️ Fornecedor novo detectado. Vamos cadastrá-lo.")
                razao_social = input("Digite a Razão Social do fornecedor: ")
                
                sql_insere_fornecedor = "INSERT INTO fornecedores (razao_social, cnpj) VALUES (%s, %s)"
                cursor.execute(sql_insere_fornecedor, (razao_social, cnpj_fornecedor))
                
                # O cursor.lastrowid pega o número do ID que o MySQL acabou de criar automaticamente
                fornecedor_id = cursor.lastrowid 
                print(f"✅ Fornecedor '{razao_social}' cadastrado com sucesso!")
           
            # Agora que temos o fornecedor_id (seja antigo ou novo), inserimos o produto
            sql = "INSERT INTO produtos (nome, quantidade, preco_custo, fornecedor_id) VALUES (%s, %s, %s, %s)"
            valores = (nome, quantidade, preco, fornecedor_id)
            
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