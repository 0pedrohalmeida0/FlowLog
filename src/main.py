from listar_produtos import listar_todos_produtos, alerta_estoque_baixo
from cadastro_interativo import cadastrar_produto_interativo
from saida_estoque import registrar_saida
from ver_historico import exibir_relatorio_movimentacoes
from gerenciar_fornecedor import listar_produtos_por_fornecedor
from entrada import entrada
from login import fazer_login
from cadastrar_usuario import cadastrar_usuario
from configurar_alerta import atualizar_alerta

def menu():
    nivel_usuario = fazer_login()
    if not nivel_usuario:
        return
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
        print("5. Listar Produtos por Fornecedor")
        print("6. Entrada de estoque")
        print("7. Cadastrar Novo Usuário (Administrador)")
        print("8. Configurar Alerta de Estoque")
        print("0. Sair")
        print("="*40)
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == "1":
            # Opção liberada para todos
            listar_todos_produtos()

        elif opcao == "2":
            # TRAVA DE SEGURANÇA
            if nivel_usuario == 1:
                print("\n⛔ Acesso Negado: Apenas usuários autorizados.")
            else:
                cadastrar_produto_interativo()

        elif opcao == "3":
            # TRAVA DE SEGURANÇA
            if nivel_usuario == 1:
                print("\n⛔ Acesso Negado: Apenas usuários autorizados.")
            else:
                registrar_saida()
                alerta_estoque_baixo()

        elif opcao == "4":
            if nivel_usuario == 1:
                print("\n⛔ Acesso Negado: Apenas usuários autorizados.")
            else:
                exibir_relatorio_movimentacoes()

        elif opcao == "5":
            listar_produtos_por_fornecedor()

        elif opcao == "6":
            if nivel_usuario == 1:
                print("\n⛔ Acesso Negado: Apenas usuários autorizados.")
            else:
                entrada()
                
        elif opcao == "7":
            # TRAVA DE SEGURANÇA SUPERIOR (NÍVEL 3)
            if nivel_usuario != 3:
                print("\n⛔ Acesso Negado: Apenas a Administração (Nível 3) pode cadastrar novos usuários.")
            else:
                cadastrar_usuario()
                
        elif opcao == "8":
            if nivel_usuario == 1:
                print("\n⛔ Acesso Negado: Apenas usuários autorizados.")
            else:
                atualizar_alerta()

        elif opcao == "0":
            print("\nEncerrando o sistema... Bom descanso!")
            break  # Aqui sim usamos o break, pois o usuário QUER sair do programa

        else:
            print("\n⚠️ Opção inválida! Tente novamente.")

if __name__ == "__main__":
    menu()