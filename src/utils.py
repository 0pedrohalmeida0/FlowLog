"""Funções utilitárias: CNPJ, hash de senha, logger nomeado e log de movimentação."""

import re

import bcrypt

from logging_config import get_logger


logger = get_logger(__name__)


# ============================================================
# CNPJ
# ============================================================

def normalize_cnpj(cnpj):
    """Remove caracteres não numéricos de um CNPJ para comparações."""
    return re.sub(r'\D', '', str(cnpj) or '')


def validar_cnpj(cnpj):
    """Valida um CNPJ pelos dígitos verificadores.

    Aceita CNPJ com ou sem máscara. Retorna True se válido, False caso contrário.
    Rejeita sequências inválidas (00000000000000, 11111111111111, etc.).
    """
    cnpj = normalize_cnpj(cnpj)

    if len(cnpj) != 14:
        return False

    # Rejeita sequências de dígitos repetidos
    if cnpj == cnpj[0] * 14:
        return False

    # Validação do primeiro dígito verificador
    pesos_dv1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos_dv1[i] for i in range(12))
    resto = soma % 11
    dv1 = 0 if resto < 2 else 11 - resto
    if int(cnpj[12]) != dv1:
        return False

    # Validação do segundo dígito verificador
    pesos_dv2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos_dv2[i] for i in range(13))
    resto = soma % 11
    dv2 = 0 if resto < 2 else 11 - resto
    if int(cnpj[13]) != dv2:
        return False

    return True


def formatar_cnpj(cnpj):
    """Aplica a máscara XX.XXX.XXX/XXXX-XX ao CNPJ (somente se tiver 14 dígitos)."""
    cnpj = normalize_cnpj(cnpj)
    if len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


# ============================================================
# Senha (bcrypt)
# ============================================================

def hash_senha(senha_plana):
    """Gera o hash bcrypt da senha em texto puro.

    Retorna bytes (compatível com colunas VARCHAR(60) em utf-8).
    """
    if not senha_plana:
        raise ValueError("Senha não pode ser vazia.")
    return bcrypt.hashpw(senha_plana.encode('utf-8'), bcrypt.gensalt())


def verificar_senha(senha_plana, hash_armazenado):
    """Compara senha plana contra hash armazenado.

    - Se o hash estiver em formato bcrypt ($2a$/$2b$/$2y$), usa bcrypt.checkpw.
    - Se o hash NÃO for bcrypt (legado em texto puro), retorna False e
      registra um WARNING no log. Isso força o recadastro do usuário.
    """
    if not senha_plana or not hash_armazenado:
        return False

    if isinstance(hash_armazenado, bytes):
        hash_str = hash_armazenado.decode('utf-8', errors='ignore')
    else:
        hash_str = str(hash_armazenado)

    if hash_str.startswith('$2'):
        try:
            return bcrypt.checkpw(senha_plana.encode('utf-8'), hash_str.encode('utf-8'))
        except (ValueError, TypeError):
            logger.exception("Falha ao verificar hash bcrypt")
            return False

    # Senha em texto puro (legado): recusa autenticar.
    logger.warning("Senha em texto puro detectada; usuário precisa ser recadastrado")
    return False


# ============================================================
# Log de movimentação
# ============================================================

def registrar_log(cursor, produto_id, tipo, quantidade, usuario_id=None):
    """Insere uma linha no histórico de movimentações usando o cursor fornecido.

    IMPORTANTE: esta função NÃO abre conexão própria. Ela deve ser chamada
    de dentro de uma transação aberta pelo chamador, garantindo que o log
    e a atualização de estoque sejam atômicos.

    Args:
        cursor: cursor MySQL ativo (de uma transação).
        produto_id: ID do produto movimentado.
        tipo: 'ENTRADA' ou 'SAIDA'.
        quantidade: quantidade movimentada (sempre > 0).
        usuario_id: ID do usuário que registrou a movimentação. Pode ser None
            apenas em logs legados; o sistema atual sempre deve fornecê-lo.
    """
    sql = (
        "INSERT INTO historico_movimentacoes "
        "(produto_id, tipo, quantidade, usuario_id) "
        "VALUES (%s, %s, %s, %s)"
    )
    cursor.execute(sql, (produto_id, tipo, quantidade, usuario_id))
