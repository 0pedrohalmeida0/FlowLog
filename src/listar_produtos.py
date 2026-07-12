"""Telas finas de listagem de produtos. Lógica em `ProdutoService`."""

from logging_config import get_logger
from services.produto_service import ProdutoService

logger = get_logger(__name__)


# ME-06: limite padrão por tela de inventário. 50 cabe confortavelmente
# no terminal e ainda permite ver o contexto.
LIMITE_PADRAO = 50


def listar_todos_produtos():
    service = ProdutoService()

    # ME-06: perguntar limite ao usuário. 0 = sem limite.
    limite_input = input(
        f"Quantos produtos mostrar? (padrão {LIMITE_PADRAO}, 0 = sem limite): "
    ).strip()
    try:
        limite = int(limite_input) if limite_input else LIMITE_PADRAO
    except ValueError:
        print("⚠️ Valor inválido. Usando padrão.")
        limite = LIMITE_PADRAO
    if limite < 0:
        limite = LIMITE_PADRAO

    try:
        produtos = service.listar_todos()
    except Exception as e:
        logger.exception("Erro ao listar produtos")
        print(f"❌ Erro ao listar produtos: {e}")
        return

    # ME-14: defensivo — em testes ou mocks, o service pode retornar
    # None. Em produção, sempre retorna lista, mas custa nada checar.
    if not produtos:
        produtos = []
    total = len(produtos)
    if limite > 0 and total > limite:
        produtos_exibidos = produtos[:limite]
        tem_mais = True
    else:
        produtos_exibidos = produtos
        tem_mais = False

    print("\n--- RELATÓRIO DE INVENTÁRIO (FLOWLOG) ---")
    print(f"{'ID':<4} | {'NOME':<25} | {'QTD':<5} | {'PREÇO':<10}")
    print("-" * 50)

    for p in produtos_exibidos:
        print(
            f"{p['id']:<4} | {p['nome']:<25} | {p['quantidade']:<5} | R$ {p['preco_custo']:<10.2f}"
        )

    print("-" * 50)
    if tem_mais:
        print(
            f"⚠️ Exibindo {len(produtos_exibidos)} de {total} produtos. "
            f"Aumente o limite para ver mais."
        )
    logger.info("Listagem de produtos exibida: %d/%d itens", len(produtos_exibidos), total)

    # Oferece export ao final
    if total > 0:
        _oferecer_export_inventario()


def _oferecer_export_inventario():
    """Oferece export do inventário completo (não filtrado)."""
    escolha = input("\nExportar inventário completo para CSV? (S/N): ").strip().upper()
    if escolha != "S":
        return
    try:
        from csv_export import exportar_inventario
        from database import Database

        db = Database()
        conn = db.connect()
        if not conn:
            print("❌ Não foi possível abrir conexão para o export.")
            return
        try:
            cursor = conn.cursor()
            exportar_inventario(cursor)
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            if conn.is_connected():
                conn.close()
    except Exception as e:
        logger.exception("Falha no export de inventário")
        print(f"❌ Erro ao exportar: {e}")


def alerta_estoque_baixo():
    """Mostra alerta de estoque crítico + sugestões de compra.

    Para cada produto com `quantidade <= alerta_minimo`, calcula
    `qtd_sugerida = max(alerta_minimo * 2 - quantidade_atual, 0)`
    (fórmula simples: repor até 2x o mínimo).
    """
    service = ProdutoService()
    try:
        produtos_baixos = service.listar_abaixo_do_minimo()
    except Exception as e:
        logger.exception("Erro ao verificar alertas de estoque")
        print(f"Erro ao verificar alertas de estoque: {e}")
        return

    if produtos_baixos:
        print("\n" + "!" * 40)
        print(" 🚨 ALERTA DE ESTOQUE CRÍTICO + SUGESTÃO DE COMPRA 🚨")
        print("!" * 40)
        for p in produtos_baixos:
            nome = p["nome"]
            qtd = p["quantidade"]
            minimo = p["alerta_minimo"]
            fornecedor = p["fornecedor"]
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


if __name__ == "__main__":
    listar_todos_produtos()
    alerta_estoque_baixo()
