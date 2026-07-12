from database import Database
from logging_config import get_logger

logger = get_logger(__name__)


# Mapeamento de opção -> tipo a filtrar. NUNCA misturamos input do usuário
# com a query SQL: o valor aqui é uma constante de código, validada por
# dicionário. O parâmetro entra na query via %s, não por concatenação.
_FILTROS_TIPO = {
    "1": None,  # tudo
    "2": "ENTRADA",
    "3": "SAIDA",
}


def exibir_relatorio_movimentacoes():
    db = Database()
    conexao = db.connect()
    if not conexao:
        return

    try:
        print("\n--- 🔍 OPÇÕES DE RELATÓRIO ---")
        print("[ 1 ] Tudo (Entradas e Saídas)")
        print("[ 2 ] Apenas Entradas")
        print("[ 3 ] Apenas Saídas")
        escolha = input("Opção: ").strip()

        tipo_filtro = _FILTROS_TIPO.get(escolha)
        if escolha not in _FILTROS_TIPO:
            print("⚠️ Opção inválida. Listando tudo.")
            tipo_filtro = None

        sql_parts = [
            """
            SELECT h.id, p.nome, h.tipo, h.quantidade, h.data_movimentacao,
                   COALESCE(u.username, '(sistema)') AS usuario
            FROM historico_movimentacoes h
            JOIN produtos p ON h.produto_id = p.id
            LEFT JOIN usuarios u ON h.usuario_id = u.id
            """,
        ]
        params = ()

        if tipo_filtro:
            sql_parts.append("WHERE UPPER(h.tipo) = %s")
            params = (tipo_filtro,)

        sql_parts.append("ORDER BY h.data_movimentacao DESC")
        sql = " ".join(sql_parts)

        cursor = conexao.cursor()
        cursor.execute(sql, params)
        logs = cursor.fetchall()

        print("\n--- 📜 HISTÓRICO DE MOVIMENTAÇÕES (FLOWLOG) ---")
        if not logs:
            print("Nenhuma movimentação encontrada para o filtro selecionado.")
        else:
            print(
                f"{'ID':<4} | {'PRODUTO':<20} | {'TIPO':<8} | {'QTD':<5} | "
                f"{'USUÁRIO':<12} | {'DATA':<16}"
            )
            print("-" * 80)
            for log in logs:
                id_log, nome_p, tipo, qtd, data, usuario = log
                data_formatada = data.strftime("%d/%m %H:%M")
                print(
                    f"{id_log:<4} | {nome_p:<20} | {tipo:<8} | {qtd:<5} | "
                    f"{usuario:<12} | {data_formatada:<16}"
                )
            print("-" * 80)
            logger.info("Histórico exibido: filtro=%s linhas=%d", escolha, len(logs))

            # Oferece export ao final
            opt = input("\nExportar este relatório para CSV? (S/N): ").strip().upper()
            if opt == "S":
                try:
                    from csv_export import exportar_historico

                    # Re-executa a query para o export (cursor foi consumido pelo fetchall)
                    exportar_historico(cursor, tipo_filtro)
                except Exception as e:
                    logger.exception("Falha no export de histórico")
                    print(f"❌ Erro ao exportar: {e}")
    except Exception as e:
        logger.exception("Erro ao gerar relatório de movimentações")
        print(f"❌ Erro ao gerar relatório: {e}")
    finally:
        if conexao and conexao.is_connected():
            conexao.close()


if __name__ == "__main__":
    exibir_relatorio_movimentacoes()
