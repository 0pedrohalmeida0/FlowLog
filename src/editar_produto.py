"""Tela de edição de produto: fina. Lógica em `ProdutoService`."""

from exceptions import NotFoundError, ValidationError
from logging_config import get_logger
from services.produto_service import ProdutoService

logger = get_logger(__name__)


# Mapeamento de opção do menu para (chave, rótulo, função de cast).
_OPCOES = {
    "1": ("nome", "Nome", str),
    "2": ("preco_custo", "Preço de custo (R$)", lambda s: float(s.replace(",", "."))),
    "3": (
        "alerta_minimo",
        "Alerta mínimo (vazio = sem alerta)",
        lambda s: int(s) if s.strip() else None,
    ),
}


def _escolher_produto(service: ProdutoService) -> int | None:
    """Pede ID do produto. Se 0, lista e pede de novo."""
    entrada = input("ID do produto a editar (0 para listar todos): ").strip()
    try:
        id_produto = int(entrada)
    except ValueError:
        print("❌ Erro: o ID deve ser um número inteiro.")
        return None
    if id_produto < 0:
        print("❌ Erro: o ID não pode ser negativo.")
        return None
    if id_produto == 0:
        # Lista e pede de novo
        produtos = service._produtos.listar_todos()  # uso interno intencional
        if not produtos:
            print("⚠️ Nenhum produto cadastrado.")
            return None
        print(f"\n{'ID':<4} | {'NOME':<30} | {'QTD':>5}")
        print("-" * 50)
        for p in produtos:
            print(f"{p['id']:<4} | {p['nome']:<30} | {p['quantidade']:>5}")
        print("-" * 50)
        entrada = input("\nDigite o ID do produto a editar: ").strip()
        try:
            id_produto = int(entrada)
        except ValueError:
            print("❌ Erro: ID inválido.")
            return None
    return id_produto


def editar_produto():
    print("\n--- ✏️ EDITAR PRODUTO ---")

    service = ProdutoService()
    produto_id = _escolher_produto(service)
    if produto_id is None:
        return

    # Mostra resumo
    try:
        atual = service._produtos.buscar_por_id(produto_id)
    except Exception as e:
        logger.exception("Erro ao buscar produto %s", produto_id)
        print(f"❌ Erro ao buscar produto: {e}")
        return

    if not atual:
        print(f"❌ Produto com ID {produto_id} não encontrado.")
        return

    print("\nProduto atual:")
    print(f"  ID:            {atual['id']}")
    print(f"  Nome:          {atual['nome']}")
    print(f"  Quantidade:    {atual['quantidade']}  (use menu 3/6 para alterar)")
    print(f"  Preço custo:   R$ {atual['preco_custo']}")
    print(
        f"  Alerta mín.:   {atual['alerta_minimo'] if atual['alerta_minimo'] is not None else '(sem alerta)'}"
    )

    # Escolha do campo
    print("\nQual campo deseja editar?")
    print("[1] Nome")
    print("[2] Preço de custo")
    print("[3] Alerta mínimo")
    print("[0] Cancelar")
    opcao = input("Opção: ").strip()

    if opcao == "0":
        print("Edição cancelada.")
        return

    if opcao not in _OPCOES:
        print("❌ Opção inválida.")
        return

    chave, rotulo, caster = _OPCOES[opcao]

    novo_str = input(f"\nNovo valor para '{rotulo}': ").strip()
    try:
        novo_valor = caster(novo_str)
    except (ValueError, TypeError) as e:
        print(f"❌ Valor inválido: {e}. Tente novamente.")
        return

    valor_atual = atual[chave]
    confirma = (
        input(
            f"\nConfirmar alteração?\n"
            f"  '{rotulo}': '{valor_atual}' → '{novo_valor}'\n"
            f"  (S/N): "
        )
        .strip()
        .upper()
    )
    if confirma != "S":
        print("Edição cancelada.")
        return

    try:
        service.editar(produto_id, {chave: novo_valor})
    except (NotFoundError, ValidationError) as e:
        print(f"❌ {e}")
    except Exception as e:
        logger.exception("Erro inesperado ao editar produto %s", produto_id)
        print(f"❌ Erro inesperado: {e}")
    else:
        print(f"\n✅ Produto ID {produto_id} atualizado com sucesso!")


if __name__ == "__main__":
    editar_produto()
