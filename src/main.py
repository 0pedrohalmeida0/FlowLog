"""Menu principal do FlowLog.

Este é o único ponto que conhece todas as opções disponíveis e seus
handlers. O controle de acesso é feito via decorator @requer_nivel —
não há mais `if nivel_usuario == 1: print("Acesso Negado")` espalhado.
"""

from auth import requer_nivel
from cadastrar_usuario import cadastrar_usuario
from cadastro_interativo import cadastrar_produto_interativo
from configurar_alerta import atualizar_alerta
from entrada import entrada
from gerenciar_fornecedor import listar_produtos_por_fornecedor
from listar_produtos import alerta_estoque_baixo, listar_todos_produtos
from logging_config import get_logger, setup_logging
from login import fazer_login
from relatorio_curva import relatorio_curva_abc
from saida_estoque import registrar_saida
from session import logout
from ver_historico import exibir_relatorio_movimentacoes


logger = get_logger(__name__)


# ============================================================
# Wrappers com RBAC
# ============================================================
# O decorator é aplicado aqui (não nos módulos de feature) para manter
# os módulos de feature testáveis e usáveis diretamente em outros pontos
# (ex: CLI, testes) sem depender do nível do usuário logado.

@requer_nivel(2)
def op_cadastrar_produto():
    cadastrar_produto_interativo()


@requer_nivel(2)
def op_registrar_saida():
    registrar_saida()
    alerta_estoque_baixo()


@requer_nivel(2)
def op_ver_historico():
    exibir_relatorio_movimentacoes()


@requer_nivel(2)
def op_entrada_estoque():
    entrada()


@requer_nivel(3)
def op_cadastrar_usuario():
    cadastrar_usuario()


@requer_nivel(2)
def op_configurar_alerta():
    atualizar_alerta()


@requer_nivel(2)
def op_relatorio_curva():
    relatorio_curva_abc()


# Tabela de opções do menu: chave -> (rótulo, handler)
# Opções 1 e 5 não têm @requer_nivel (acessíveis a qualquer usuário logado).
MENU_OPCOES = {
    "1": ("Listar Produtos", listar_todos_produtos),
    "2": ("Cadastrar Novo Produto", op_cadastrar_produto),
    "3": ("Registrar Saída (Baixa)", op_registrar_saida),
    "4": ("Ver Histórico de Movimentações", op_ver_historico),
    "5": ("Listar Produtos por Fornecedor", listar_produtos_por_fornecedor),
    "6": ("Entrada de estoque", op_entrada_estoque),
    "7": ("Cadastrar Novo Usuário (Administrador)", op_cadastrar_usuario),
    "8": ("Configurar Alerta de Estoque", op_configurar_alerta),
    "9": ("Relatório de Curva ABC (Giro de Estoque)", op_relatorio_curva),
}


def _imprimir_menu():
    print("\n" + "=" * 40)
    print("       FLOWLOG - GESTÃO DE ESTOQUE")
    print("=" * 40)
    for chave, (rotulo, _) in MENU_OPCOES.items():
        print(f"{chave}. {rotulo}")
    print("0. Sair")
    print("=" * 40)


def menu():
    setup_logging()
    logger.info("Iniciando FlowLog")

    nivel = fazer_login()
    if not nivel:
        logger.warning("Login falhou; encerrando")
        return

    # O alerta roda aqui, uma única vez ao iniciar
    alerta_estoque_baixo()

    while True:
        _imprimir_menu()
        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == "0":
            logger.info("Encerrando sistema")
            print("\nEncerrando o sistema... Bom descanso!")
            logout()
            break

        if opcao not in MENU_OPCOES:
            print("\n⚠️ Opção inválida! Tente novamente.")
            continue

        _, handler = MENU_OPCOES[opcao]
        handler()


if __name__ == "__main__":
    menu()
