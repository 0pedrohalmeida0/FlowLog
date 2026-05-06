from listar_produtos import listar_todos_produtos
from cadastro_interativo import cadastrar_produto_interativo
from saida_estoque import registrar_saida

def menu():
    while True:
        print("\n=== SISTEMA FLOWLOG - CONTROLE DE ESTOQUE ===")
        print("1. Listar Produtos")
        print("2. Cadastrar Novo Produto")
        print("3. Registrar Saída (Baixa)")
        print("0. Sair")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == "1":
            listar_todos_produtos()
        elif opcao == "2":
            cadastrar_produto_interativo()
        elif opcao == "3":
            registrar_saida()
        elif opcao == "0":
            print("Encerrando o sistema... Até logo!")
            break
        else:
            print("Opção inválida! Tente novamente.")

if __name__ == "__main__":
    menu()