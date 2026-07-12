"""Relatório de Curva ABC (Pareto) de saídas de estoque.

A Curva ABC classifica os produtos em três faixas com base no percentual
acumulado de volume de saída:

  - A: produtos responsáveis pelos primeiros 80% do volume de saída
       (alto giro, foco principal do planejamento físico).
  - B: produtos responsáveis pelos próximos 15% (80% a 95%).
  - C: produtos responsáveis pelos 5% finais (baixo giro, candidatos
       a descontinuação ou redução de estoque de segurança).

Implementação via window function (SUM ... OVER ORDER BY) — o percentual
acumulado é calculado no próprio banco, sem N+1 queries.
"""

from database import Database
from logging_config import get_logger

logger = get_logger(__name__)


# Query: calcula total de saídas por produto, ordena desc, calcula
# percentual individual e acumulado, e classifica em A/B/C.
# CTEs mantêm a leitura clara mesmo em queries analíticas longas.
_SQL_CURVA_ABC = """
WITH saidas_por_produto AS (
    SELECT
        p.id          AS produto_id,
        p.nome        AS nome,
        COALESCE(SUM(h.quantidade), 0) AS total_saidas
    FROM produtos p
    LEFT JOIN historico_movimentacoes h
        ON h.produto_id = p.id
       AND UPPER(h.tipo) = 'SAIDA'
    GROUP BY p.id, p.nome
),
total_geral AS (
    SELECT COALESCE(SUM(total_saidas), 0) AS total
    FROM saidas_por_produto
    WHERE total_saidas > 0
),
ranking AS (
    SELECT
        s.produto_id,
        s.nome,
        s.total_saidas,
        SUM(s.total_saidas) OVER (ORDER BY s.total_saidas DESC) AS acumulado
    FROM saidas_por_produto s
    WHERE s.total_saidas > 0
)
SELECT
    r.nome,
    r.total_saidas,
    ROUND(r.total_saidas / tg.total * 100, 2)        AS percentual,
    ROUND(r.acumulado    / tg.total * 100, 2)        AS percentual_acumulado,
    CASE
        WHEN r.acumulado / tg.total <= 0.80 THEN 'A'
        WHEN r.acumulado / tg.total <= 0.95 THEN 'B'
        ELSE 'C'
    END                                              AS classificacao
FROM ranking r
CROSS JOIN total_geral tg
ORDER BY r.total_saidas DESC
"""


def _classificacao_legenda(classe):
    """Devolve descrição legível da classe para o relatório."""
    return {
        "A": "A — alto giro (até 80% do volume)",
        "B": "B — giro intermediário (80% a 95%)",
        "C": "C — baixo giro (acima de 95%)",
    }.get(classe, classe)


def relatorio_curva_abc():
    print("\n--- 📊 RELATÓRIO DE CURVA ABC (GIRO DE ESTOQUE) ---")

    db = Database()
    conexao = db.connect()
    if not conexao:
        return

    try:
        cursor = conexao.cursor()
        cursor.execute(_SQL_CURVA_ABC)
        resultados = cursor.fetchall()
        cursor.close()

        if not resultados:
            print(
                "⚠️ Nenhuma saída registrada no histórico. Faça ao menos uma saída para gerar a Curva ABC."
            )
            return

        print(f"{'CLASSE':<4} | {'PRODUTO':<28} | {'SAÍDAS':>6} | " f"{'%':>6} | {'% ACUM.':>8}")
        print("-" * 70)

        for classe, nome, total, pct, pct_acum in (
            (r[4], r[0], r[1], r[2], r[3]) for r in resultados
        ):
            print(
                f"{classe:<4} | {nome[:28]:<28} | {total:>6} | " f"{pct:>5.2f}% | {pct_acum:>7.2f}%"
            )
        print("-" * 70)

        # Resumo executivo: quantos produtos em cada classe
        contagem = {"A": 0, "B": 0, "C": 0}
        for r in resultados:
            contagem[r[4]] = contagem.get(r[4], 0) + 1

        print("\nResumo:")
        for classe in ("A", "B", "C"):
            if contagem.get(classe, 0) > 0:
                print(f"  • {contagem[classe]:>3} produto(s) {_classificacao_legenda(classe)}")

        logger.info(
            "Curva ABC gerada: %d produtos (A=%d, B=%d, C=%d)",
            len(resultados),
            contagem.get("A", 0),
            contagem.get("B", 0),
            contagem.get("C", 0),
        )
    except Exception as e:
        logger.exception("Erro ao gerar Curva ABC")
        print(f"❌ Erro ao gerar relatório: {e}")
    finally:
        if conexao and conexao.is_connected():
            conexao.close()


if __name__ == "__main__":
    relatorio_curva_abc()
