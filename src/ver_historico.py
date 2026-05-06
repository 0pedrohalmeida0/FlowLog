from database import Database

def exibir_relatorio_movimentacoes():
    db = Database()
    conexao = db.connect()
    
    if conexao:
        try:
            cursor = conexao.cursor()
            
            # SQL com JOIN para trazer o nome do produto em vez de apenas o ID
            sql = """
            SELECT h.id, p.nome, h.tipo, h.quantidade, h.data_movimentacao 
            FROM historico_movimentacoes h
            JOIN produtos p ON h.produto_id = p.id
            ORDER BY h.data_movimentacao DESC
            """
            
            cursor.execute(sql)
            logs = cursor.fetchall()
            
            print("\n--- 📜 HISTÓRICO DE MOVIMENTAÇÕES (FLOWLOG) ---")
            print(f"{'ID':<4} | {'PRODUTO':<20} | {'TIPO':<8} | {'QTD':<5} | {'DATA':<16}")
            print("-" * 65)
            
            for log in logs:
                id_log, nome_p, tipo, qtd, data = log
                # Formatando a data para algo mais amigável (Dia/Mês Hora:Min)
                data_formatada = data.strftime("%d/%m %H:%M")
                
                print(f"{id_log:<4} | {nome_p:<20} | {tipo:<8} | {qtd:<5} | {data_formatada}")
            
            print("-" * 65)
            
            cursor.close()
            conexao.close()
            
        except Exception as e:
            print(f"❌ Erro ao gerar relatório: {e}")

if __name__ == "__main__":
    exibir_relatorio_movimentacoes()