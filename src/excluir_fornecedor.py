from database import Database
from logging_config import get_logger

logger = get_logger(__name__)


def _parse_id_positivo(prompt):
    """Lê um ID do usuário, garantindo que seja um inteiro positivo."""
    entrada = input(prompt).strip()
    try:
        id_val = int(entrada)
    except ValueError:
        print("❌ Erro: o ID deve ser um número inteiro.")
        return None
    if id_val <= 0:
        print("❌ Erro: o ID deve ser positivo.")
        return None
    return id_val


def excluir_fornecedor():
    print("\n--- 🗑️ EXCLUIR FORNECEDOR ---")
    id_alvo = _parse_id_positivo("Digite o ID do fornecedor que deseja excluir: ")
    if id_alvo is None:
        return

    db = Database()
    conexao = db.connect()
    if not conexao:
        return

    try:
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM fornecedores WHERE id = %s", (id_alvo,))
        conexao.commit()

        if cursor.rowcount > 0:
            logger.info("Fornecedor ID=%d excluído", id_alvo)
            print("✅ Fornecedor excluído com sucesso!")
        else:
            print("⚠️ Nenhum fornecedor encontrado com esse ID.")
    except Exception as e:
        try:
            conexao.rollback()
        except Exception:
            pass
        erro_texto = str(e).lower()
        if "foreign key" in erro_texto:
            logger.warning("Tentativa de excluir fornecedor ID=%d com produtos vinculados", id_alvo)
            print(
                "❌ Não é possível excluir este fornecedor porque ele está associado a produtos. Por favor, remova ou altere os produtos relacionados antes de tentar novamente."
            )
        else:
            logger.exception("Erro ao excluir fornecedor ID=%d", id_alvo)
            print(f"❌ Ocorreu um erro ao tentar excluir o fornecedor: {e}")
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        if conexao and conexao.is_connected():
            conexao.close()
