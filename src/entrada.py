"""Tela de entrada de estoque: fina. Lógica em `EstoqueService`."""

from exceptions import EstoqueInsuficienteError, NotFoundError, ValidationError
from logging_config import get_logger
from services.estoque_service import EstoqueService

logger = get_logger(__name__)


def entrada():
    """Coleta input do usuário, chama o service, traduz exceções."""
    print("\n--- ENTRADA DE PRODUTO FLOWLOG ---")

    try:
        id_produto = int(input("Digite o ID do produto que está chegando: "))
        quantidade = int(input("Quantidade a ser adicionada ao estoque: "))
    except ValueError:
        print("❌ Erro: nos campos de ID e quantidade, use apenas números inteiros.")
        return

    try:
        service = EstoqueService()
        resultado = service.registrar_entrada(id_produto, quantidade)
    except ValidationError as e:
        print(f"❌ {e}")
    except NotFoundError as e:
        print(f"❌ {e}")
    except EstoqueInsuficienteError as e:
        # Improvável em entrada, mas defensivo
        print(f"⚠️ {e}")
    except Exception as e:
        logger.exception("Erro inesperado durante entrada")
        print(f"❌ Erro inesperado: {e}")
    else:
        print("📜 Movimentação registrada no histórico.")
        print(
            f"\n✅ Entrada registrada! {resultado['nome']}: "
            f"{resultado['qtd_anterior']} -> {resultado['qtd_nova']}"
        )


if __name__ == "__main__":
    entrada()
