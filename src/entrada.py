from database import Database
from logging_config import get_logger
from session import usuario_id_atual
from utils import registrar_log


logger = get_logger(__name__)


def entrada():
    """Registra uma entrada de estoque com transação atômica.

    O UPDATE em `produtos` e o INSERT em `historico_movimentacoes` acontecem
    na mesma transação: ou ambos gravam, ou nenhum grava. Resolve o bug
    anterior em que o sistema poderia cair entre as duas conexões e
    deixar o estoque sem o respectivo log.
    """
    with Database().transaction() as (conn, cursor):
        print("\n--- ENTRADA DE PRODUTO FLOWLOG ---")

        try:
            id_produto = int(input("Digite o ID do produto que está chegando: "))
            quantidade_entrada = int(input("Quantidade a ser adicionada ao estoque: "))
        except ValueError:
            print("❌ Erro: nos campos de ID e quantidade, use apenas números inteiros.")
            return

        if quantidade_entrada <= 0:
            print("❌ Erro: a quantidade de entrada deve ser maior que zero.")
            return

        # SELECT FOR UPDATE trava a linha durante a transação,
        # impedindo que duas entradas simultâneas gerem saldo errado.
        cursor.execute(
            "SELECT nome, quantidade FROM produtos WHERE id = %s FOR UPDATE",
            (id_produto,),
        )
        produto = cursor.fetchone()

        if not produto:
            print(f"\n❌ Erro: Produto com ID {id_produto} não encontrado no inventário.")
            return

        nome_atual, qtd_atual = produto
        nova_quantidade = qtd_atual + quantidade_entrada

        cursor.execute(
            "UPDATE produtos SET quantidade = %s WHERE id = %s",
            (nova_quantidade, id_produto),
        )

        # Mesmo cursor = mesma transação = commit atômico no __exit__.
        usuario_id = usuario_id_atual()
        registrar_log(cursor, id_produto, 'ENTRADA', quantidade_entrada, usuario_id)

        logger.info(
            "Entrada registrada: produto_id=%d qtd=+%d usuario_id=%s",
            id_produto, quantidade_entrada, usuario_id,
        )
        print("📜 Movimentação registrada no histórico.")
        print(f"\n✅ Entrada registrada! {nome_atual}: {qtd_atual} -> {nova_quantidade}")


if __name__ == "__main__":
    entrada()
