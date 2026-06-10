from database import Database

def relatorio_curva_abc():
    print("\n--- 📊 RELATÓRIO DE CURVA ABC (PRODUTOS COM MAIOR SAÍDA) ---")
    
    db = Database()
    conexao = db.connect()
    
    if conexao:
        try:
            cursor = conexao.cursor()
            
            sql = """
            SELECT produtos.nome, SUM(historico_movimentacoes.quantidade) as total_saido
            FROM historico_movimentacoes
            INNER JOIN produtos ON historico_movimentacoes.produto_id = produtos.id
            WHERE UPPER(historico_movimentacoes.tipo) = 'SAIDA'
            GROUP BY produtos.nome
            ORDER BY total_saido DESC
            """
            
            cursor.execute(sql)
            resultados = cursor.fetchall()
            
            if resultados:
                print(f"{'POSIÇÃO':<10} | {'PRODUTO':<30} | {'TOTAL DE SAÍDAS':<15}")
                print("-" * 60)
                
                for posicao, linha in enumerate(resultados, start=1):
                    nome_produto = linha[0]
                    total_saido = linha[1]
                    print(f"{posicao:<10} | {nome_produto:<30} | {total_saido:<15}")
            else:
                print("⚠️ Nenhum registro de saída encontrado no histórico.")
                
            cursor.close()
            conexao.close()
            
        except Exception as e:
            print(f"❌ Erro ao gerar relatório: {e}")