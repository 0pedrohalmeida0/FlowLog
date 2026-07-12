from database import Database


# Mapeamento de opção -> tipo a filtrar. NUNCA misturamos input do usuário
# com a query SQL: o valor aqui é uma constante de código, validada por
# dicionário. O parâmetro entra na query via %s, não por concatenação.
_FILTROS_TIPO = {
    "1": None,        # tudo
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

        # Query construída por partes, sem f-string concatenando input.
        sql_parts = [
            """
            SELECT h.id, p.nome, h.tipo, h.quantidade, h.data_movimentacao
            FROM historico_movimentacoes h
            JOIN produtos p ON h.produto_id = p.id
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
        cursor.close()

        # ==========================================
        # Exibição dos dados
        # ==========================================
        print("\n--- 📜 HISTÓRICO DE MOVIMENTAÇÕES (FLOWLOG) ---")
        if not logs:
            print("Nenhuma movimentação encontrada para o filtro selecionado.")
        else:
            print(f"{'ID':<4} | {'PRODUTO':<20} | {'TIPO':<8} | {'QTD':<5} | {'DATA':<16}")
            print("-" * 65)
            for log in logs:
                id_log, nome_p, tipo, qtd, data = log
                data_formatada = data.strftime("%d/%m %H:%M")
                print(f"{id_log:<4} | {nome_p:<20} | {tipo:<8} | {qtd:<5} | {data_formatada}")
            print("-" * 65)

    except Exception as e:
        print(f"❌ Erro ao gerar relatório: {e}")
    finally:
        if conexao and conexao.is_connected():
            conexao.close()


if __name__ == "__main__":
    exibir_relatorio_movimentacoes()
