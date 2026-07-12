"""Funções utilitárias: CNPJ, hash de senha, validação de complexidade e log."""

import hashlib
import re

import bcrypt

from logging_config import get_logger

logger = get_logger(__name__)


# ============================================================
# CNPJ
# ============================================================


def normalize_cnpj(cnpj):
    """Remove caracteres não numéricos de um CNPJ para comparações.

    CR-07: aceita apenas dígitos ASCII 0-9. Dígitos Unicode
    (árabe ٠١٢٣٤٥٦٧٨٩, etc) são rejeitados via str.isdigit().
    """
    if cnpj is None:
        raise ValueError("CNPJ não pode ser None.")
    s = str(cnpj)
    # CR-07: filtra caracteres não-ASCII para evitar duplicação
    # silenciosa entre "123" (ASCII) e "١٢٣" (Unicode).
    # isdigit() aceita '٠'-'٩' (True), por isso usamos regex ASCII.
    s = re.sub(r"[^0-9]", "", s)
    if not s and cnpj:
        raise ValueError(
            f"CNPJ contém apenas caracteres não-ASCII: {cnpj!r}. " f"Use apenas dígitos 0-9."
        )
    return s


def validar_cnpj(cnpj):
    """Valida um CNPJ pelos dígitos verificadores.

    Aceita CNPJ com ou sem máscara. Retorna True se válido, False caso contrário.
    Rejeita sequências inválidas (00000000000000, 11111111111111, etc.)
    e CNPJs com dígitos não-ASCII (CR-07).
    """
    # CR-07: rejeita CNPJ None ou só com chars não-ASCII
    if cnpj is None or (isinstance(cnpj, str) and not cnpj.strip()):
        return False
    try:
        cnpj = normalize_cnpj(cnpj)
    except ValueError:
        return False

    if not cnpj or len(cnpj) != 14:
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
# Senha (bcrypt + complexidade)
# ============================================================

# Requisitos mínimos para uma senha ser aceita.
# Configure no .env se quiser ajustar (v1.4+).
MIN_SENHA_LEN = 6


# CR-03: bcrypt impõe limite de 72 bytes. Senhas longas (com acentos
# ou emoji) estouram e geram ValueError. Pré-normalizamos com SHA-256
# (que devolve 32 bytes hex) para aceitar senhas arbitrariamente longas
# mantendo bcrypt como fator de trabalho (work factor).
# A mesma transformação é usada em hash e em verify.
def _pre_normalizar_senha(senha_plana) -> bytes:
    """Reduz a senha para 32 bytes (SHA-256 hex) antes de passar ao bcrypt.

    bcrypt opera com no máximo 72 bytes. Se a senha exceder, usamos
    SHA-256 como pré-normalização: o hash é determinístico, então o mesmo
    pré-processamento em hash_senha/verificar_senha dá match.

    ME-11: aceita str ou bytes. str é codificado em UTF-8; bytes é
    usado como está (assume que já está em UTF-8).
    """
    if isinstance(senha_plana, bytes):
        data = senha_plana
    else:
        data = str(senha_plana).encode("utf-8")
    return hashlib.sha256(data).hexdigest().encode("ascii")


def hash_senha(senha_plana):
    """Gera o hash bcrypt da senha em texto puro.

    Retorna bytes (compatível com colunas VARCHAR(60) em utf-8).
    """
    if not senha_plana:
        raise ValueError("Senha não pode ser vazia.")
    return bcrypt.hashpw(_pre_normalizar_senha(senha_plana), bcrypt.gensalt())


def verificar_senha(senha_plana, hash_armazenado):
    """Compara senha plana contra hash armazenado.

    - Se o hash estiver em formato bcrypt ($2a$/$2b$/$2y$), usa bcrypt.checkpw.
    - Se o hash NÃO for bcrypt (legado em texto puro), retorna False e
      registra um WARNING no log. Isso força o recadastro do usuário.
    """
    if not senha_plana or not hash_armazenado:
        return False

    if isinstance(hash_armazenado, bytes):
        hash_str = hash_armazenado.decode("utf-8", errors="ignore")
    else:
        hash_str = str(hash_armazenado)

    if hash_str.startswith("$2"):
        try:
            return bcrypt.checkpw(_pre_normalizar_senha(senha_plana), hash_str.encode("utf-8"))
        except (ValueError, TypeError):
            logger.exception("Falha ao verificar hash bcrypt")
            return False

    # Senha em texto puro (legado): recusa autenticar.
    # ME-15: chamamos bcrypt.checkpw com um hash dummy para mitigar
    # timing attack (não vaza se o hash é bcrypt ou plaintext pela
    # diferença de tempo de resposta).
    logger.warning("Senha em texto puro detectada; usuário precisa ser recadastrado")
    try:
        bcrypt.checkpw(_pre_normalizar_senha(senha_plana), b"$2b$12$" + b"x" * 53)
    except Exception:
        pass
    return False


def validar_senha_complexidade(senha):
    """Valida os requisitos mínimos de complexidade da senha.

    Regras atuais (v1.2):
        - Mínimo 6 caracteres
        - Pelo menos 1 letra (a-zA-Z)
        - Pelo menos 1 dígito (0-9)

    Returns:
        (ok: bool, mensagem: str) — quando ok=False, mensagem explica o motivo.
    """
    # ME-11: aceita apenas str. Se vier bytes, retorna erro
    # (em vez de explodir com TypeError no re.search).
    if isinstance(senha, bytes):
        try:
            senha = senha.decode("utf-8")
        except UnicodeDecodeError:
            return False, "Senha contém bytes inválidos."
    if not isinstance(senha, str):
        return False, "Senha deve ser uma string."

    if not senha:
        return False, "A senha não pode ser vazia."

    if len(senha) < MIN_SENHA_LEN:
        return False, f"A senha deve ter no mínimo {MIN_SENHA_LEN} caracteres."

    if not re.search(r"[a-zA-Z]", senha):
        return False, "A senha deve conter pelo menos uma letra."

    if not re.search(r"\d", senha):
        return False, "A senha deve conter pelo menos um número."

    return True, ""


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
