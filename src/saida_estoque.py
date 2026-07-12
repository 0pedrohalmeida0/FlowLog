"""Tela de saída de estoque: fina. Lógica em `EstoqueService`."""

from exceptions import EstoqueInsuficienteError, NotFoundError, ValidationError
from logging_config import get_logger
from services.estoque_service import EstoqueService

logger = get_logger(__name__)


def registrar_saida():
    """Coleta input, chama o service, traduz exceções."""
    try:
        id_produto = int(input("Digite o ID do produto que está saindo: "))
        quantidade = int(input("Quantidade para retirar do estoque: "))
    except ValueError:
        print("❌ Erro: Digite apenas números inteiros para ID e Quantidade.")
        return

    try:
        service = EstoqueService()
        resultado = service.registrar_saida(id_produto, quantidade)
    except ValidationError as e:
        print(f"❌ {e}")
    except NotFoundError as e:
        print(f"❌ {e}")
    except EstoqueInsuficienteError as e:
        print(f"\n⚠️ {e}")
    except Exception as e:
        logger.exception("Erro inesperado durante saída")
        print(f"❌ Erro inesperado: {e}")
    else:
        print("📜 Movimentação registrada no histórico.")
        print(
            f"\n✅ Saída registrada! {resultado['nome']}: "
            f"{resultado['qtd_anterior']} -> {resultado['qtd_nova']}"
        )


if __name__ == "__main__":
    registrar_saida()
