from database import Database
from logging_config import get_logger
from session import usuario_id_atual
from utils import registrar_log

logger = get_logger(__name__)


def registrar_saida():
    """Registra uma saída de estoque com transação atômica.

    Trava a linha do produto com SELECT ... FOR UPDATE antes de subtrair,
    evitando race condition em saídas concorrentes. UPDATE e INSERT no
    histórico rodam na mesma transação.
    """
    with Database().transaction() as (conn, cursor):
        try:
            id_produto = int(input("Digite o ID do produto que está saindo: "))
            quantidade_saida = int(input("Quantidade para retirar do estoque: "))
        except ValueError:
            print("❌ Erro: Digite apenas números inteiros para ID e Quantidade.")
            return

        if quantidade_saida <= 0:
            print("❌ Erro: a quantidade de saída deve ser maior que zero.")
            return

        cursor.execute(
            "SELECT nome, quantidade FROM produtos WHERE id = %s FOR UPDATE",
            (id_produto,),
        )
        produto = cursor.fetchone()

        if not produto:
            print("\n❌ Produto não encontrado.")
            return

        nome_atual, qtd_atual = produto

        if qtd_atual < quantidade_saida:
            print(f"\n⚠️ Estoque insuficiente! Saldo atual: {qtd_atual}")
            return

        nova_qtd = qtd_atual - quantidade_saida
        cursor.execute(
            "UPDATE produtos SET quantidade = %s WHERE id = %s",
            (nova_qtd, id_produto),
        )

        usuario_id = usuario_id_atual()
        registrar_log(cursor, id_produto, "SAIDA", quantidade_saida, usuario_id)

        logger.info(
            "Saída registrada: produto_id=%d qtd=-%d usuario_id=%s",
            id_produto,
            quantidade_saida,
            usuario_id,
        )
        print("📜 Movimentação registrada no histórico.")
        print(f"\n✅ Saída registrada! {nome_atual}: {qtd_atual} -> {nova_qtd}")


if __name__ == "__main__":
    registrar_saida()
