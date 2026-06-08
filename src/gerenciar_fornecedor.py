from database import Database
from utils import normalize_cnpj

def listar_produtos_por_fornecedor():
    db = Database()
    conexao = db.connect()
    
    if conexao:
        try:
            print("\n--- LISTAR PRODUTOS POR FORNECEDOR ---")
            cnpj_alvo = normalize_cnpj(input("Digite o CNPJ do fornecedor: "))
            
            cursor = conexao.cursor()
            
            # PASSO 1: Buscar o fornecedor pelo CNPJ 
            sql_busca_fornec = (
                "SELECT id, razao_social FROM fornecedores "
                "WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), ' ', '') = %s"
            )
            cursor.execute(sql_busca_fornec, (cnpj_alvo,))
            fornecedor = cursor.fetchone()
            
            if not fornecedor:
                print("❌ Fornecedor não encontrado.")
                cursor.close()
                conexao.close()
                return
            
            fornecedor_id = fornecedor[0]
            razao_social = fornecedor[1]
            
            print(f"\n📦 Produtos do fornecedor: {razao_social}")
           
            # PASSO 2: Buscar os produtos vinculados a esse fornecedor            
            sql_busca_produtos = "SELECT nome, quantidade, preco_custo FROM produtos WHERE fornecedor_id = %s"
            valores = (fornecedor_id,)
            
            cursor.execute(sql_busca_produtos, valores)
            
            # PASSO 3: Buscar tudo e exibir
            # fetchall() retorna uma lista de tuplas: [('Teclado', 10, 50.0), ('Mouse', 5, 20.0)]
            produtos = cursor.fetchall()
            
            if produtos:
                for produto in produtos:
                    # produto[0] é o nome, produto[1] é a qtde, produto[2] é o preço
                    print(f"- {produto[0]} | Estoque: {produto[1]} | Custo: R$ {produto[2]}")
            else:
                print("Este fornecedor ainda não possui produtos cadastrados no inventário.")
                
            cursor.close()
            conexao.close()
            
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    listar_produtos_por_fornecedor()