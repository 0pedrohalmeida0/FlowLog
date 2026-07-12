from database import Database
from utils import normalize_cnpj, validar_cnpj, formatar_cnpj


def cadastrar_produto_interativo():
    print("\n--- CADASTRO DE PRODUTO FLOWLOG ---")

    nome = input("Digite o nome do produto: ").strip()
    if not nome:
        print("❌ Erro: o nome do produto não pode ser vazio.")
        return

    try:
        quantidade = int(input("Digite a quantidade em estoque: "))
        if quantidade < 0:
            print("❌ Erro: a quantidade não pode ser negativa.")
            return
        preco = float(input("Digite o preço de custo (ex: 10.50): "))
        if preco < 0:
            print("❌ Erro: o preço não pode ser negativo.")
            return
    except ValueError:
        print("❌ Erro: nos campos quantidade e preço, use apenas números.")
        return

    # Coleta o alerta mínimo (loop limpo, sem código morto após o break).
    alerta_minimo = None
    while True:
        resposta = input(
            "Deseja configurar um alerta de estoque mínimo para este produto? (S/N): "
        ).strip().upper()
        if resposta == "S":
            try:
                alerta_minimo = int(input("Digite a quantidade mínima para alerta: "))
                if alerta_minimo < 0:
                    print("❌ Erro: o alerta mínimo não pode ser negativo.")
                    return
                break
            except ValueError:
                print("❌ Erro: digite um número inteiro válido.")
                return
        elif resposta == "N":
            break
        else:
            print("Resposta inválida. Digite apenas 'S' ou 'N'.")

    # Coleta e valida o CNPJ
    cnpj_input = input("Digite o CNPJ do fornecedor: ").strip()
    if not validar_cnpj(cnpj_input):
        print("❌ Erro: CNPJ inválido. Verifique os dígitos e tente novamente.")
        return
    cnpj_fornecedor = normalize_cnpj(cnpj_input)

    # Conexão única para fornecedor + produto (insert atômico)
    db = Database()
    conexao = db.connect()
    if not conexao:
        return

    try:
        cursor = conexao.cursor()

        # 1. Verifica se o fornecedor já existe pelo CNPJ normalizado
        sql_busca_fornecedor = (
            "SELECT id FROM fornecedores "
            "WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), ' ', '') = %s"
        )
        cursor.execute(sql_busca_fornecedor, (cnpj_fornecedor,))
        resultado = cursor.fetchone()

        if resultado:
            fornecedor_id = resultado[0]
            print(f"👉 Fornecedor já cadastrado encontrado (ID: {fornecedor_id}).")
        else:
            print("\nℹ️ Fornecedor novo detectado. Vamos cadastrá-lo.")
            razao_social = input("Digite a Razão Social do fornecedor: ").strip()
            if not razao_social:
                print("❌ Erro: a razão social não pode ser vazia.")
                return

            cursor.execute(
                "INSERT INTO fornecedores (razao_social, cnpj) VALUES (%s, %s)",
                (razao_social, cnpj_fornecedor),
            )
            fornecedor_id = cursor.lastrowid
            print(f"✅ Fornecedor '{razao_social}' cadastrado com sucesso!")

        # 2. Insere o produto vinculado ao fornecedor
        cursor.execute(
            "INSERT INTO produtos (nome, quantidade, preco_custo, fornecedor_id, alerta_minimo) "
            "VALUES (%s, %s, %s, %s, %s)",
            (nome, quantidade, preco, fornecedor_id, alerta_minimo),
        )
        conexao.commit()

        print(f"\n✅ Sucesso! '{nome}' foi adicionado ao inventário.")
        print(f"   Fornecedor: {formatar_cnpj(cnpj_fornecedor)}")

    except Exception as e:
        try:
            conexao.rollback()
        except Exception:
            pass
        print(f"❌ Erro inesperado: {e}")
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        if conexao and conexao.is_connected():
            conexao.close()


if __name__ == "__main__":
    cadastrar_produto_interativo()
