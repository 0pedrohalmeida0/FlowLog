from database import Database

def atualizar_alerta():
    print("\n--- 🔔 CONFIGURAR ALERTA DE ESTOQUE ---")
    id_produto = input("Digite o ID do produto que deseja configurar: ")
    
    # Pergunta o novo valor (aceitando 0 caso ele queira remover o alerta)
    novo_alerta = input("Digite a nova quantidade mínima (ou deixe em branco para remover o alerta): ")
    
    # Tratamento lógico: se ele apertar ENTER vazio, transformamos em None (que vira NULL no banco)
    if novo_alerta == "":
        novo_alerta = None
    else:
        novo_alerta = int(novo_alerta)
        
    db = Database()
    conexao = db.connect()
    
    if conexao:
        try:
            cursor = conexao.cursor()
            
            sql = "UPDATE produtos SET alerta_minimo = %s WHERE id = %s"
            
            # A ordem da tupla TEM QUE SER a mesma ordem dos %s no SQL
            cursor.execute(sql, (novo_alerta, id_produto))
            conexao.commit()
            
            # Verifica se o banco realmente achou aquele ID e alterou
            if cursor.rowcount > 0:
                print(f"✅ Sucesso! Alerta atualizado para o produto ID {id_produto}.")
            else:
                print("⚠️ Produto não encontrado. Verifique o ID.")
                
            cursor.close()
            conexao.close()
            
        except Exception as e:
            print(f"❌ Erro ao atualizar alerta: {e}")

if __name__ == "__main__":
    atualizar_alerta()