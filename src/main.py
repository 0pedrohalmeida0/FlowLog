"""Menu principal do FlowLog.

Este é o único ponto que conhece todas as opções disponíveis e seus
handlers. O controle de acesso é feito via decorator @requer_nivel —
não há mais `if nivel_usuario == 1: print("Acesso Negado")` espalhado.

Comportamentos de sessão (v1.2):
    - Login falho: re-prompt (não encerra o sistema). Digite 'Q' no usuário
      para sair.
    - Auto-logout por inatividade: SESSION_TIMEOUT_MINUTES (env) minutos sem
      interação encerra a sessão e volta para a tela de login.
"""

import os

from auth import requer_nivel
from backup import menu_backup
from cadastrar_usuario import cadastrar_usuario
from cadastro_interativo import cadastrar_produto_interativo
from configurar_alerta import atualizar_alerta
from csv_import import importar_produtos_csv
from editar_produto import editar_produto
from entrada import entrada
from gerenciar_fornecedor import listar_produtos_por_fornecedor
from listar_produtos import alerta_estoque_baixo, listar_todos_produtos
from logging_config import get_logger, setup_logging
from login import fazer_login
from relatorio_curva import relatorio_curva_abc
from saida_estoque import registrar_saida
from session import logout, registrar_atividade, sessao_expirada
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


@requer_nivel(2)
def op_editar_produto():
    editar_produto()


@requer_nivel(2)
def op_importar_csv():
    importar_produtos_csv()


@requer_nivel(2)
def op_backup():
    menu_backup()


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
    "10": ("Editar Produto", op_editar_produto),
    "11": ("Importar Produtos de CSV", op_importar_csv),
    "12": ("Backup e Restauração", op_backup),
}


def _session_timeout():
    """Lê o timeout de sessão do .env (0 = desabilitado)."""
    try:
        return int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    except ValueError:
        return 30


def _imprimir_menu():
    print("\n" + "=" * 40)
    print("       FLOWLOG - GESTÃO DE ESTOQUE")
    print("=" * 40)
    for chave, (rotulo, _) in MENU_OPCOES.items():
        print(f"{chave}. {rotulo}")
    print("0. Sair")
    print("=" * 40)


def _loop_menu():
    """Loop interno do menu. Retorna quando o usuário sai ou a sessão expira."""
    while True:
        timeout = _session_timeout()
        if timeout > 0 and sessao_expirada(timeout):
            logger.info("Sessão expirada por inatividade (timeout=%d min)", timeout)
            print("\n⏰ Sessão expirada por inatividade. Faça login novamente.")
            logout()
            return

        registrar_atividade()
        _imprimir_menu()
        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == "0":
            logger.info("Encerrando sistema")
            print("\nEncerrando o sistema... Bom descanso!")
            logout()
            return

        if opcao not in MENU_OPCOES:
            print("\n⚠️ Opção inválida! Tente novamente.")
            continue

        _, handler = MENU_OPCOES[opcao]
        handler()
        # Cada ação do usuário reseta o timer de inatividade
        registrar_atividade()


def menu():
    setup_logging()
    logger.info("Iniciando FlowLog")

    # Loop externo: re-prompt no login até dar certo ou o usuário pedir pra sair
    while True:
        nivel = fazer_login()
        if nivel is None:
            # Login falhou; perguntar se quer tentar de novo
            escolha = (
                input("\nPressione ENTER para tentar novamente, ou Q para sair: ").strip().upper()
            )
            if escolha == "Q":
                logger.info("Usuário encerrou o sistema após falha de login")
                print("\nAté logo!")
                return
            continue

        # Login OK; rodar alerta de estoque baixo e entrar no menu
        alerta_estoque_baixo()
        _loop_menu()


if __name__ == "__main__":
    menu()
