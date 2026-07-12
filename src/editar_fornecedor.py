from database import Database
from utils import normalize_cnpj, validar_cnpj, formatar_cnpj


def gerenciar_fornecedor_interativo():
    print("\n--- GERENCIAR FORNECEDOR ---")

    cnpj_input = input("Digite o CNPJ do fornecedor que deseja gerenciar: ").strip()
    if not validar_cnpj(cnpj_input):
        print("❌ CNPJ inválido. Verifique os dígitos e tente novamente.")
        return

    cnpj_alvo = normalize_cnpj(cnpj_input)

    db = Database()
    conexao = db.connect()
    if not conexao:
        return

    try:
        cursor = conexao.cursor()
        sql_busca = (
            "SELECT id, razao_social FROM fornecedores "
            "WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), ' ', '') = %s"
        )
        cursor.execute(sql_busca, (cnpj_alvo,))
        resultado = cursor.fetchone()

        if not resultado:
            print(f"❌ Fornecedor não encontrado com este CNPJ ({formatar_cnpj(cnpj_alvo)}).")
            return

        fornecedor_id, razao_social_atual = resultado
        print(f"\n👉 Fornecedor encontrado: {razao_social_atual} (ID: {fornecedor_id})")
        print("Escolha uma ação:")
        print("[ 1 ] Editar Razão Social")
        print("[ 2 ] Excluir Fornecedor")

        acao = input("Opção: ").strip()

        if acao == '1':
            nova_razao = input(
                f"Digite a nova Razão Social (atual é '{razao_social_atual}'): "
            ).strip()
            if not nova_razao:
                print("❌ Erro: razão social não pode ser vazia.")
                return

            cursor.execute(
                "UPDATE fornecedores SET razao_social = %s WHERE id = %s",
                (nova_razao, fornecedor_id),
            )
            conexao.commit()
            print(f"✅ Sucesso! Razão social atualizada para '{nova_razao}'.")

        elif acao == '2':
            confirmacao = input(
                f"⚠️ Tem certeza que deseja excluir '{razao_social_atual}'? (S/N): "
            ).strip().upper()

            if confirmacao == 'S':
                try:
                    cursor.execute(
                        "DELETE FROM fornecedores WHERE id = %s",
                        (fornecedor_id,),
                    )
                    conexao.commit()
                    if cursor.rowcount > 0:
                        print("✅ Fornecedor excluído com sucesso!")
                    else:
                        print("⚠️ Nenhum fornecedor foi excluído.")
                except Exception as e:
                    try:
                        conexao.rollback()
                    except Exception:
                        pass
                    erro_texto = str(e).lower()
                    if "foreign key" in erro_texto:
                        print("❌ Não é possível excluir: este fornecedor possui produtos cadastrados no estoque.")
                    else:
                        print(f"❌ Erro ao excluir: {e}")
            else:
                print("Ação de exclusão cancelada.")
        else:
            print("❌ Opção inválida.")

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        if conexao and conexao.is_connected():
            conexao.close()


if __name__ == "__main__":
    gerenciar_fornecedor_interativo()
