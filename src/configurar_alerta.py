from database import Database
from logging_config import get_logger


logger = get_logger(__name__)


def atualizar_alerta():
    print("\n--- 🔔 CONFIGURAR ALERTA DE ESTOQUE ---")
    id_input = input("Digite o ID do produto que deseja configurar: ").strip()
    try:
        id_produto = int(id_input)
    except ValueError:
        print("❌ Erro: o ID deve ser um número inteiro.")
        return
    if id_produto <= 0:
        print("❌ Erro: o ID deve ser positivo.")
        return

    # Pergunta o novo valor (aceitando vazio caso ele queira remover o alerta)
    novo_alerta_input = input(
        "Digite a nova quantidade mínima (ou deixe em branco para remover o alerta): "
    ).strip()

    if novo_alerta_input == "":
        novo_alerta = None
    else:
        try:
            novo_alerta = int(novo_alerta_input)
        except ValueError:
            print("❌ Erro: a quantidade mínima deve ser um número inteiro.")
            return
        if novo_alerta < 0:
            print("❌ Erro: a quantidade mínima não pode ser negativa.")
            return

    db = Database()
    conexao = db.connect()
    if not conexao:
        return

    try:
        cursor = conexao.cursor()
        cursor.execute(
            "UPDATE produtos SET alerta_minimo = %s WHERE id = %s",
            (novo_alerta, id_produto),
        )
        conexao.commit()

        if cursor.rowcount > 0:
            logger.info("Alerta do produto ID=%d atualizado para %s", id_produto, novo_alerta)
            print(f"✅ Sucesso! Alerta atualizado para o produto ID {id_produto}.")
        else:
            print("⚠️ Produto não encontrado. Verifique o ID.")
    except Exception as e:
        try:
            conexao.rollback()
        except Exception:
            pass
        logger.exception("Erro ao atualizar alerta do produto ID=%d", id_produto)
        print(f"❌ Erro ao atualizar alerta: {e}")
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        if conexao and conexao.is_connected():
            conexao.close()


if __name__ == "__main__":
    atualizar_alerta()
