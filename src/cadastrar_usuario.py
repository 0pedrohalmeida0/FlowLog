from database import Database

def cadastrar_usuario():
    print("\n--- 🛡️ CADASTRO DE NOVOS USUÁRIOS (ACESSO RESTRITO) ---")
    
    # 1. Captura os dados com os inputs
    novo_username = input("Digite o nome do novo usuário: ")
    nova_senha = input("Digite a senha de acesso: ")
    
    try:
        # Força o int() para não quebrar a lógica matemática do seu Menu
        nivel = int(input("Nível de acesso (1 - Operador | 2 - Gerente | 3 - Admin): "))
    except ValueError:
        print("❌ Erro: Digite apenas números para o nível de acesso.")
        return

    # 2. Conecta e salva
    db = Database()
    conexao = db.connect()
    
    if conexao:
        try:
            cursor = conexao.cursor()
            
            # 3. O comando SQL com os marcadores de segurança (%s)
            sql = "INSERT INTO usuarios (username, senha, nivel_acesso) VALUES (%s, %s, %s)"
            cursor.execute(sql, (novo_username, nova_senha, nivel))
            
            conexao.commit()
            print(f"\n✅ Sucesso! O usuário '{novo_username}' foi cadastrado com Nível {nivel}.")
            
            cursor.close()
            conexao.close()
            
        except Exception as e:
            # Se o usuário tentar cadastrar um username que já existe, o MySQL barra por causa do "UNIQUE" que criamos antes.
            print(f"\n❌ Falha ao cadastrar (Usuário já existe?): {e}")

if __name__ == "__main__":
    cadastrar_usuario()