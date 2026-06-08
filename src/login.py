from database import Database

def fazer_login():
    db = Database()
    conexao = db.connect()
    
    if conexao:
        try:
            print("\n🔒 TELA DE LOGIN - FLOWLOG")
            usuario_digitado = input("Usuário: ")
            senha_digitada = input("Senha: ")
            
            cursor = conexao.cursor()
            
            # Busca o nível de acesso APENAS SE o usuário e a senha baterem
            sql = "SELECT nivel_acesso FROM usuarios WHERE username = %s AND senha = %s"
            cursor.execute(sql, (usuario_digitado, senha_digitada))
            
            resultado = cursor.fetchone()
            
            cursor.close()
            conexao.close()
            
            if resultado:
                # Tupla descompactada
                nivel = resultado[0]
                print(f"✅ Login aprovado! Bem-vindo(a), {usuario_digitado}. (Nível {nivel})")
                return nivel
            else:
                print("❌ Usuário ou senha incorretos.")
                return None
                
        except Exception as e:
            print(f"❌ Erro no banco: {e}")
            return None