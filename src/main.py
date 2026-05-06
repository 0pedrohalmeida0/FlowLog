from listar_produtos import listar_todos_produtos, alerta_estoque_baixo
from cadastro_interativo import cadastrar_produto_interativo
from saida_estoque import registrar_saida
from ver_historico import exibir_relatorio_movimentacoes

def menu():
    # 1. O alerta roda aqui, uma única vez ao iniciar
    alerta_estoque_baixo()
    
    # 2. O programa entra no loop infinito do menu
    while True:
        print("\n" + "="*40)
        print("       FLOWLOG - GESTÃO DE ESTOQUE")
        print("="*40)
        print("1. Listar Produtos")
        print("2. Cadastrar Novo Produto")
        print("3. Registrar Saída (Baixa)")
        print("4. Ver Histórico de Movimentações")
        print("0. Sair")
        print("="*40)
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == "1":
            listar_todos_produtos()
        elif opcao == "2":
            cadastrar_produto_interativo()
        elif opcao == "3":
            registrar_saida()
            # Opcional: rodar o alerta de novo após uma saída para atualizar
            alerta_estoque_baixo() 
        elif opcao == "4":
            exibir_relatorio_movimentacoes()
        elif opcao == "0":
            print("\nEncerrando o sistema... Bom descanso, Pedro!")
            break
        else:
            print("\n⚠️ Opção inválida! Tente novamente.")

if __name__ == "__main__":
    menu()