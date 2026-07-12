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
        cursor.execute("SELECT id, nome, quantidade, preco_custo, data_entrada FROM produtos")
        resultados = cursor.fetchall()

        print("\n--- RELATÓRIO DE INVENTÁRIO (FLOWLOG) ---")
        print(f"{'ID':<4} | {'NOME':<25} | {'QTD':<5} | {'PREÇO':<10}")
        print("-" * 50)

        for produto in resultados:
            id_p, nome, qtd, preco, data = produto
            print(f"{id_p:<4} | {nome:<25} | {qtd:<5} | R$ {preco:<10.2f}")

        print("-" * 50)
        logger.info("Listagem de produtos exibida: %d itens", len(resultados))

        # Oferece export ao final
        if resultados:
            _oferecer_export_inventario_com_cursor(cursor, resultados)
    except Exception as e:
        logger.exception("Erro ao listar produtos")
        print(f"❌ Erro ao listar produtos: {e}")
    finally:
        if conexao and conexao.is_connected():
            conexao.close()


def _oferecer_export_inventario_com_cursor(cursor, resultados):
    """Oferece export reutilizando o cursor ainda aberto (mesma conexão)."""
    escolha = input("\nExportar listagem para CSV? (S/N): ").strip().upper()
    if escolha != "S":
        return
    try:
        from csv_export import exportar_inventario

        exportar_inventario(cursor)
    except Exception as e:
        logger.exception("Falha no export de inventário")
        print(f"❌ Erro ao exportar: {e}")


def alerta_estoque_baixo():
    """Mostra alerta de estoque crítico + sugestões de compra.

    Para cada produto com `quantidade <= alerta_minimo`, calcula
    `qtd_sugerida = max(alerta_minimo * 2 - quantidade_atual, 0)`
    (fórmula simples: repor até 2x o mínimo).
    """
    db = Database()
    conexao = db.connect()

    if not conexao:
        return

    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT p.nome, p.quantidade, p.alerta_minimo,
                   COALESCE(f.razao_social, '(sem fornecedor)') AS fornecedor
            FROM produtos p
            LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
            WHERE p.alerta_minimo IS NOT NULL
              AND p.quantidade <= p.alerta_minimo
            ORDER BY (p.alerta_minimo - p.quantidade) DESC
            """)
        produtos_baixos = cursor.fetchall()

        if produtos_baixos:
            print("\n" + "!" * 40)
            print(" 🚨 ALERTA DE ESTOQUE CRÍTICO + SUGESTÃO DE COMPRA 🚨")
            print("!" * 40)
            for nome, qtd, minimo, fornecedor in produtos_baixos:
                qtd_sugerida = max(minimo * 2 - qtd, 0)
                print(
                    f"⚠️ {nome}: {qtd} restantes (mín. {minimo})  → "
                    f"pedir {qtd_sugerida} do fornecedor '{fornecedor}'"
                )
            print("!" * 40 + "\n")
            logger.warning(
                "Alerta de estoque crítico: %d produto(s) abaixo do mínimo",
                len(produtos_baixos),
            )
    except Exception as e:
        logger.exception("Erro ao verificar alertas de estoque")
        print(f"Erro ao verificar alertas de estoque: {e}")
    finally:
        if conexao and conexao.is_connected():
            conexao.close()


if __name__ == "__main__":
    listar_todos_produtos()
    alerta_estoque_baixo()
