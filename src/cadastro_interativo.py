"""Tela de cadastro de produto: fina. Lógica em `ProdutoService`."""

from exceptions import CNPJInvalidoError, ValidationError
from logging_config import get_logger
from services.produto_service import ProdutoService
from utils import formatar_cnpj

logger = get_logger(__name__)


def _perguntar_alerta_minimo() -> int | None:
    """Loop que pergunta se quer alerta, e se sim, pede o valor."""
    while True:
        resposta = (
            input("Deseja configurar um alerta de estoque mínimo para este produto? (S/N): ")
            .strip()
            .upper()
        )
        if resposta == "S":
            try:
                valor = int(input("Digite a quantidade mínima para alerta: "))
                if valor < 0:
                    print("❌ Erro: o alerta mínimo não pode ser negativo.")
                    continue
                return valor
            except ValueError:
                print("❌ Erro: digite um número inteiro válido.")
        elif resposta == "N":
            return None
        else:
            print("Resposta inválida. Digite apenas 'S' ou 'N'.")


def cadastrar_produto_interativo():
    print("\n--- CADASTRO DE PRODUTO FLOWLOG ---")

    nome = input("Digite o nome do produto: ").strip()
    if not nome:
        print("❌ Erro: o nome do produto não pode ser vazio.")
        return

    try:
        quantidade = int(input("Digite a quantidade em estoque: "))
        preco = float(input("Digite o preço de custo (ex: 10.50): "))
    except ValueError:
        print("❌ Erro: nos campos quantidade e preço, use apenas números.")
        return

    alerta_minimo = _perguntar_alerta_minimo()
    cnpj_input = input("Digite o CNPJ do fornecedor: ").strip()

    try:
        service = ProdutoService()
        novo_id = service.cadastrar(
            nome=nome,
            quantidade=quantidade,
            preco_custo=preco,
            fornecedor_cnpj=cnpj_input,
            alerta_minimo=alerta_minimo,
        )
    except CNPJInvalidoError as e:
        print(f"❌ {e}")
    except ValidationError as e:
        print(f"❌ {e}")
    except Exception as e:
        logger.exception("Erro inesperado durante cadastro")
        print(f"❌ Erro inesperado: {e}")
    else:
        print(f"\n✅ Sucesso! Produto ID {novo_id} ('{nome}') adicionado ao inventário.")
        print(f"   Fornecedor: {formatar_cnpj(cnpj_input)}")


if __name__ == "__main__":
    cadastrar_produto_interativo()
