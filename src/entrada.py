from database import Database
from utils import registrar_log

def entrada():
    db = Database()
    conexao = db.connect()
    
    if conexao:
        try:
            print("\n--- ENTRADA DE PRODUTO FLOWLOG ---")
            
            # 1. Padroniza a busca: Agora por ID 
            id_produto = int(input("Digite o ID do produto que está chegando: "))
            quantidade_entrada = int(input("Quantidade a ser adicionada ao estoque: "))
            
            cursor = conexao.cursor()
            
            # 2. Buscamos o produto pelo ID
            sql_busca_produto = "SELECT nome, quantidade FROM produtos WHERE id = %s"
            cursor.execute(sql_busca_produto, (id_produto,))
            produto = cursor.fetchone() 
            
            if produto:
                nome_atual, qtd_atual = produto
                nova_quantidade = qtd_atual + quantidade_entrada
                
                # 3. Atualiza a quantidade do produto no banco
                sql_atualiza_produto = "UPDATE produtos SET quantidade = %s WHERE id = %s"
                cursor.execute(sql_atualiza_produto, (nova_quantidade, id_produto))
                
                # 4. SALVA AS ALTERAÇÕES NO BANCO
                conexao.commit()
                
                # Usa a palavra 'ENTRADA' em maiúsculo para manter o padrão do utils.py
                registrar_log(id_produto, 'ENTRADA', quantidade_entrada)
                
                print("📜 Movimentação registrada no histórico.")
                print(f"\n✅ Entrada registrada! {nome_atual}: {qtd_atual} -> {nova_quantidade}")
            else:
                print(f"\n❌ Erro: Produto com ID {id_produto} não encontrado no inventário.")
            
            cursor.close()
            conexao.close()
            
        except ValueError:
            print("❌ Erro: Nos campos de ID e quantidade, use apenas números inteiros.")
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    entrada()