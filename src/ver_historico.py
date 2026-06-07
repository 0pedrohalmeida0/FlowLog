from database import Database

def exibir_relatorio_movimentacoes():
    db = Database()
    conexao = db.connect()
    
    if conexao:
        try:
            cursor = conexao.cursor()
            

            # 1. MENU DE FILTRO

            print("\n--- 🔍 OPÇÕES DE RELATÓRIO ---")
            print("[ 1 ] Tudo (Entradas e Saídas)")
            print("[ 2 ] Apenas Entradas")
            print("[ 3 ] Apenas Saídas")
            escolha = input("Opção: ")
            

            # 2. LÓGICA DO FILTRO NO SQL

            # 2. LÓGICA DO FILTRO NO SQL (CORRIGIDA)
            if escolha == "2":
                # UPPER() garante que ele ache 'Entrada', 'ENTRADA' ou 'entrada'
                filtro_sql = "WHERE UPPER(h.tipo) = 'ENTRADA'"
            elif escolha == "3": 
                filtro_sql = "WHERE UPPER(h.tipo) = 'SAIDA'" 
            else:
                filtro_sql = ""
            
            # Note o 'f' no início das aspas para permitir a injeção da variável {filtro_sql}
            sql = f"""
            SELECT h.id, p.nome, h.tipo, h.quantidade, h.data_movimentacao 
            FROM historico_movimentacoes h
            JOIN produtos p ON h.produto_id = p.id
            {filtro_sql}
            ORDER BY h.data_movimentacao DESC
            """
            
            cursor.execute(sql)
            logs = cursor.fetchall()
            
            # ==========================================
            # 3. EXIBIÇÃO DOS DADOS
            # ==========================================
            print("\n--- 📜 HISTÓRICO DE MOVIMENTAÇÕES (FLOWLOG) ---")
            
            # Uma pequena trava de segurança caso a busca não retorne nada
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
            
            cursor.close()
            conexao.close()
            
        except Exception as e:
            print(f"❌ Erro ao gerar relatório: {e}")

if __name__ == "__main__":
    exibir_relatorio_movimentacoes()