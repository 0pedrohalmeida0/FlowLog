from database import Database

def registrar_saida():
    db = Database()
    conexao = db.connect()
    
    if conexao:
        try:
            cursor = conexao.cursor()
            
            # 1. Identificamos o produto e a quantidade de saída
            id_produto = int(input("Digite o ID do produto que está saindo: "))
            quantidade_saida = int(input("Quantidade para retirar do estoque: "))
            
            # 2. Primeiro, verificamos se o produto existe e se tem estoque suficiente
            cursor.execute("SELECT nome, quantidade FROM produtos WHERE id = %s", (id_produto,))
            produto = cursor.fetchone()
            
            if produto:
                nome_atual, qtd_atual = produto
                
                if qtd_atual >= quantidade_saida:
                    # 3. Fazemos a subtração (UPDATE)
                    nova_qtd = qtd_atual - quantidade_saida
                    sql = "UPDATE produtos SET quantidade = %s WHERE id = %s"
                    cursor.execute(sql, (nova_qtd, id_produto))
                    
                    conexao.commit()
                    print(f"\n✅ Saída registrada! {nome_atual}: {qtd_atual} -> {nova_qtd}")
                else:
                    print(f"\n⚠️ Estoque insuficiente! Saldo atual: {qtd_atual}")
            else:
                print("\n❌ Produto não encontrado.")
            
            cursor.close()
            conexao.close()
            
        except ValueError:
            print("❌ Erro: Digite apenas números inteiros para ID e Quantidade.")
        except Exception as e:
            print(f"❌ Erro na operação: {e}")

if __name__ == "__main__":
    registrar_saida()