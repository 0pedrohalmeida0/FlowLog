from database import Database
from utils import normalize_cnpj, validar_cnpj, formatar_cnpj


def listar_produtos_por_fornecedor():
    print("\n--- LISTAR PRODUTOS POR FORNECEDOR ---")
    cnpj_input = input("Digite o CNPJ do fornecedor: ").strip()

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

        # PASSO 1: Buscar o fornecedor pelo CNPJ normalizado
        sql_busca_fornec = (
            "SELECT id, razao_social FROM fornecedores "
            "WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), ' ', '') = %s"
        )
        cursor.execute(sql_busca_fornec, (cnpj_alvo,))
        fornecedor = cursor.fetchone()

        if not fornecedor:
            print(f"❌ Fornecedor não encontrado para o CNPJ {formatar_cnpj(cnpj_alvo)}.")
            return

        fornecedor_id, razao_social = fornecedor

        print(f"\n📦 Produtos do fornecedor: {razao_social}")

        # PASSO 2: Buscar os produtos vinculados a esse fornecedor
        cursor.execute(
            "SELECT nome, quantidade, preco_custo FROM produtos WHERE fornecedor_id = %s",
            (fornecedor_id,),
        )
        produtos = cursor.fetchall()
        cursor.close()

        if produtos:
            for produto in produtos:
                nome, qtd, preco = produto
                print(f"- {nome} | Estoque: {qtd} | Custo: R$ {preco:.2f}")
        else:
            print("Este fornecedor ainda não possui produtos cadastrados no inventário.")

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
    finally:
        if conexao and conexao.is_connected():
            conexao.close()


if __name__ == "__main__":
    listar_produtos_por_fornecedor()
