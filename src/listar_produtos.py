from database import Database
from logging_config import get_logger


logger = get_logger(__name__)


def listar_todos_produtos():
    db = Database()
    conexao = db.connect()

    if not conexao:
        return

    try:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT id, nome, quantidade, preco_custo, data_entrada FROM produtos"
        )
        resultados = cursor.fetchall()
        cursor.close()

        print("\n--- RELATÓRIO DE INVENTÁRIO (FLOWLOG) ---")
        print(f"{'ID':<4} | {'NOME':<25} | {'QTD':<5} | {'PREÇO':<10}")
        print("-" * 50)

        for produto in resultados:
            id_p, nome, qtd, preco, data = produto
            print(f"{id_p:<4} | {nome:<25} | {qtd:<5} | R$ {preco:<10.2f}")

        print("-" * 50)
        logger.info("Listagem de produtos exibida: %d itens", len(resultados))
    except Exception as e:
        logger.exception("Erro ao listar produtos")
        print(f"❌ Erro ao listar produtos: {e}")
    finally:
        if conexao and conexao.is_connected():
            conexao.close()


def alerta_estoque_baixo():
    db = Database()
    conexao = db.connect()

    if not conexao:
        return

    try:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT nome, quantidade, alerta_minimo FROM produtos "
            "WHERE alerta_minimo IS NOT NULL AND quantidade <= alerta_minimo"
        )
        produtos_baixos = cursor.fetchall()
        cursor.close()

        if produtos_baixos:
            print("\n" + "!" * 40)
            print(" 🚨 ALERTA DE ESTOQUE CRÍTICO 🚨")
            print("!" * 40)
            for produto in produtos_baixos:
                nome, qtd, minimo = produto
                print(f"⚠️ {nome}: Restam apenas {qtd} unidades! (Mínimo: {minimo})")
            print("!" * 40 + "\n")
            logger.warning("Alerta de estoque crítico: %d produto(s) abaixo do mínimo",
                           len(produtos_baixos))
    except Exception as e:
        logger.exception("Erro ao verificar alertas de estoque")
        print(f"Erro ao verificar alertas de estoque: {e}")
    finally:
        if conexao and conexao.is_connected():
            conexao.close()


if __name__ == "__main__":
    listar_todos_produtos()
    alerta_estoque_baixo()
