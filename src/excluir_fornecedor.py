from database import Database

def excluir_fornecedor():
    print("\n--- 🗑️ EXCLUIR FORNECEDOR ---")
    id_alvo = input("Digite o ID do fornecedor que deseja excluir: ")
    
    db = Database()
    conexao = db.connect()
    
    if conexao:
        try:
            cursor = conexao.cursor()
            
            # Tentamos apagar direto (Abordagem Reativa - EAFP)
            sql = "DELETE FROM fornecedores WHERE id = %s"
            cursor.execute(sql, (id_alvo,))
            conexao.commit()
            
            # Se o rowcount for maior que 0, significa que apagou de fato
            if cursor.rowcount > 0:
                print("✅ Fornecedor excluído com sucesso!")
            else:
                print("⚠️ Nenhum fornecedor encontrado com esse ID.")
                
            cursor.close()
            conexao.close()
            
        except Exception as e:
            erro_texto = str(e)
            if "foreign key constraint" in erro_texto.lower():
                print("❌ Não é possível excluir este fornecedor porque ele está associado a produtos. Por favor, remova ou altere os produtos relacionados antes de tentar novamente.")
            else:
                print(f"❌ Ocorreu um erro ao tentar excluir o fornecedor: {e}")
