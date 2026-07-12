"""Edição de produtos com snapshot de auditoria.

Edita nome, preço de custo e alerta mínimo. NÃO edita quantidade
diretamente — alterações de quantidade devem passar pelo fluxo de
entrada/saída para preservar o histórico de movimentações.

Cada edição grava um snapshot do produto antes e depois na tabela
`produtos_historico_edicoes` (JSON), com referência ao usuário.
"""

import json
from decimal import Decimal

from database import Database
from logging_config import get_logger
from session import usuario_id_atual

logger = get_logger(__name__)


def _parse_alerta(s):
    """Aceita vazio (None), número inteiro positivo."""
    s = s.strip()
    if s == "":
        return None
    n = int(s)
    if n < 0:
        raise ValueError("alerta mínimo não pode ser negativo")
    return n


# Campos editáveis: (coluna_no_banco, rótulo_amigável, função de cast)
_CAMPOS_EDITAVEIS = {
    "1": ("nome", "Nome", str),
    "2": ("preco_custo", "Preço de custo (R$)", lambda s: float(s.replace(",", "."))),
    "3": ("alerta_minimo", "Alerta mínimo (vazio = sem alerta)", _parse_alerta),
}


def _serializar_produto(row):
    """Converte um row do MySQL em dict JSON-serializável."""
    return {
        "id": row[0],
        "nome": row[1],
        "quantidade": row[2],
        "preco_custo": float(row[3]) if isinstance(row[3], Decimal) else row[3],
        "fornecedor_id": row[4],
        "alerta_minimo": row[5],
    }


def editar_produto():
    print("\n--- ✏️ EDITAR PRODUTO ---")
    id_input = input("ID do produto a editar (0 para listar todos): ").strip()
    try:
        id_produto = int(id_input)
    except ValueError:
        print("❌ Erro: o ID deve ser um número inteiro.")
        return
    if id_produto < 0:
        print("❌ Erro: o ID não pode ser negativo.")
        return

    db = Database()
    conexao = db.connect()
    if not conexao:
        return

    try:
        cursor = conexao.cursor()

        if id_produto == 0:
            # Listar todos para o usuário escolher
            cursor.execute(
                "SELECT id, nome, quantidade, preco_custo, fornecedor_id, alerta_minimo "
                "FROM produtos ORDER BY id"
            )
            produtos = cursor.fetchall()
            if not produtos:
                print("⚠️ Nenhum produto cadastrado.")
                return
            print(f"\n{'ID':<4} | {'NOME':<30} | {'QTD':>5}")
            print("-" * 50)
            for p in produtos:
                print(f"{p[0]:<4} | {p[1]:<30} | {p[2]:>5}")
            print("-" * 50)
            id_input = input("\nDigite o ID do produto a editar: ").strip()
            try:
                id_produto = int(id_input)
            except ValueError:
                print("❌ Erro: ID inválido.")
                return

        # Lê o produto atual
        cursor.execute(
            "SELECT id, nome, quantidade, preco_custo, fornecedor_id, alerta_minimo "
            "FROM produtos WHERE id = %s",
            (id_produto,),
        )
        produto = cursor.fetchone()

        if not produto:
            print(f"❌ Produto com ID {id_produto} não encontrado.")
            return

        # Mostra resumo
        print("\nProduto atual:")
        print(f"  ID:            {produto[0]}")
        print(f"  Nome:          {produto[1]}")
        print(f"  Quantidade:    {produto[2]}  (use menu 3/6 para alterar)")
        print(f"  Preço custo:   R$ {produto[3]}")
        print(f"  Alerta mín.:   {produto[5] if produto[5] is not None else '(sem alerta)'}")

        # Pergunta qual campo editar
        print("\nQual campo deseja editar?")
        print("[1] Nome")
        print("[2] Preço de custo")
        print("[3] Alerta mínimo")
        print("[0] Cancelar")
        opcao = input("Opção: ").strip()

        if opcao == "0":
            print("Edição cancelada.")
            return

        if opcao not in _CAMPOS_EDITAVEIS:
            print("❌ Opção inválida.")
            return

        coluna, rotulo, caster = _CAMPOS_EDITAVEIS[opcao]

        # Lê e valida o novo valor
        while True:
            novo_valor_str = input(f"\nNovo valor para '{rotulo}': ").strip()
            try:
                novo_valor = caster(novo_valor_str)
                break
            except ValueError as e:
                print(f"❌ Valor inválido: {e}. Tente novamente.")

        # Confirma
        valor_atual = produto[_COLUNA_PARA_IDX[coluna]]
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

        # Grava snapshot ANTES, atualiza, grava snapshot DEPOIS, commita tudo
        snapshot_antes = _serializar_produto(produto)

        cursor.execute(
            f"UPDATE produtos SET {coluna} = %s WHERE id = %s",
            (novo_valor, id_produto),
        )

        cursor.execute(
            "SELECT id, nome, quantidade, preco_custo, fornecedor_id, alerta_minimo "
            "FROM produtos WHERE id = %s",
            (id_produto,),
        )
        produto_novo = cursor.fetchone()
        snapshot_depois = _serializar_produto(produto_novo)

        uid = usuario_id_atual()
        cursor.execute(
            "INSERT INTO produtos_historico_edicoes "
            "(produto_id, usuario_id, snapshot_antes, snapshot_depois) "
            "VALUES (%s, %s, %s, %s)",
            (
                id_produto,
                uid,
                json.dumps(snapshot_antes, ensure_ascii=False),
                json.dumps(snapshot_depois, ensure_ascii=False),
            ),
        )
        conexao.commit()
        logger.info(
            "Produto ID=%d editado: campo=%s usuario_id=%s",
            id_produto,
            coluna,
            uid,
        )
        print(f"\n✅ Produto ID {id_produto} atualizado com sucesso!")

    except Exception as e:
        try:
            conexao.rollback()
        except Exception:
            pass
        logger.exception("Erro ao editar produto ID=%s", id_produto)
        print(f"❌ Erro ao editar produto: {e}")
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        if conexao and conexao.is_connected():
            conexao.close()


# Mapeamento coluna -> índice no SELECT (id, nome, quantidade, preco_custo, fornecedor_id, alerta_minimo)
_COLUNA_PARA_IDX = {
    "nome": 1,
    "preco_custo": 3,
    "alerta_minimo": 5,
}


if __name__ == "__main__":
    editar_produto()
