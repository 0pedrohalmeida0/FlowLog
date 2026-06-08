from database import Database
from utils import normalize_cnpj

def gerenciar_fornecedor_interativo():
    db = Database()
    conexao = db.connect()
    
    if conexao:
        try:
            print("\n--- GERENCIAR FORNECEDOR ---")
            
            # 1. Busca o fornecedor pelo CNPJ
            cnpj_alvo = normalize_cnpj(input("Digite o CNPJ do fornecedor que deseja gerenciar: "))
            
            cursor = conexao.cursor()
            sql_busca = (
                "SELECT id, razao_social FROM fornecedores "
                "WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), ' ', '') = %s"
            )
            cursor.execute(sql_busca, (cnpj_alvo,))
            resultado = cursor.fetchone()
            
            # Se o resultado for None, o fornecedor não existe
            if not resultado:
                print("❌ Fornecedor não encontrado com este CNPJ.")
                cursor.close()
                conexao.close()
                return # Encerra a função aqui
            
            # Desempacota a tupla retornada pelo MySQL
            fornecedor_id = resultado[0]
            razao_social_atual = resultado[1]
            
            print(f"\n👉 Fornecedor encontrado: {razao_social_atual} (ID: {fornecedor_id})")
            print("Escolha uma ação:")
            print("[ 1 ] Editar Razão Social")
            print("[ 2 ] Excluir Fornecedor")
            
            acao = input("Opção: ")
            
            # Edição de fornecedor
            if acao == '1':
                nova_razao = input(f"Digite a nova Razão Social (atual é '{razao_social_atual}'): ")
                
                sql_update = "UPDATE fornecedores SET razao_social = %s WHERE id = %s"
                cursor.execute(sql_update, (nova_razao, fornecedor_id))
                conexao.commit()
                
                print(f"✅ Sucesso! Razão social atualizada para '{nova_razao}'.")

            #Exclusão de fornecedor
            elif acao == '2':
                confirmacao = input(f"⚠️ Tem certeza que deseja excluir '{razao_social_atual}'? (S/N): ").upper()
                
                if confirmacao == 'S':
                    try:
                        sql_delete = "DELETE FROM fornecedores WHERE id = %s"
                        cursor.execute(sql_delete, (fornecedor_id,))
                        conexao.commit()
                        print("✅ Fornecedor excluído com sucesso!")
                        
                    except Exception as e:
                        # Este erro geralmente ocorre por causa da Chave Estrangeira (produtos vinculados)
                        print(f"❌ Erro ao excluir: Este fornecedor possui produtos cadastrados no estoque.")
                        print(f"Detalhe técnico: {e}")
                else:
                    print("Ação de exclusão cancelada.")
            
            else:
                print("❌ Opção inválida.")
                
            cursor.close()
            conexao.close()
            
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    gerenciar_fornecedor_interativo()