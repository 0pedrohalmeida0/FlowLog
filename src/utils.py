from database import Database

def registrar_log(produto_id, tipo, quantidade):
    db = Database()
    conexao = db.connect()
    if conexao:
        try:
            cursor = conexao.cursor()
            sql = "INSERT INTO historico_movimentacoes (produto_id, tipo, quantidade) VALUES (%s, %s, %s)"
            cursor.execute(sql, (produto_id, tipo, quantidade))
            conexao.commit()
            cursor.close()
            conexao.close()
        except Exception as e:
            print(f"Erro ao gravar log: {e}")