"""Testes unitários de utils.py: CNPJ, bcrypt, validação de complexidade."""

import pytest

from utils import (
    formatar_cnpj,
    hash_senha,
    normalize_cnpj,
    validar_cnpj,
    validar_senha_complexidade,
    verificar_senha,
)

# ============================================================
# CNPJ
# ============================================================


class TestCNPJ:
    """Validação de CNPJ por dígitos verificadores."""

    def test_cnpj_valido_com_mascara(self):
        assert validar_cnpj("11.222.333/0001-81") is True

    def test_cnpj_valido_sem_mascara(self):
        assert validar_cnpj("11222333000181") is True

    def test_cnpj_petrobras_valido(self):
        # CNPJ público da Petrobras, dígitos verificadores corretos
        assert validar_cnpj("33.000.167/0001-01") is True

    def test_cnpj_digitos_arabicos_rejeitado_cr07(self):
        """CR-07: CNPJ escrito com dígitos arábicos (Unicode) deve
        ser rejeitado para evitar duplicação silenciosa.
        """
        # 33.000.167/0001-01 em arábico
        cnpj_arabic = "٣٣٠٠٠١٦٧٠٠٠١٠١"
        assert validar_cnpj(cnpj_arabic) is False
        with pytest.raises(ValueError):
            normalize_cnpj(cnpj_arabic)

    def test_cnpj_misto_ascii_arabic_rejeitado_cr07(self):
        """CR-07: mistura ASCII+árabe também rejeitada."""
        # 13 dígitos ASCII + 1 arábico
        cnpj_misto = "11.222.333/0001-8١"
        assert validar_cnpj(cnpj_misto) is False

    def test_cnpj_none_rejeitado_ba09(self):
        """BA-09: CNPJ None deve levantar erro, não retornar string vazia."""
        assert validar_cnpj(None) is False
        with pytest.raises(ValueError):
            normalize_cnpj(None)

    def test_cnpj_string_vazia_rejeitado(self):
        assert validar_cnpj("") is False
        assert validar_cnpj("   ") is False

    def test_cnpj_bradesco_valido(self):
        assert validar_cnpj("60.746.948/0001-12") is True

    def test_cnpj_dv_invalido(self):
        assert validar_cnpj("11.222.333/0001-00") is False
        assert validar_cnpj("11.222.333/0001-82") is False

    def test_cnpj_tamanho_invalido(self):
        assert validar_cnpj("123") is False
        assert validar_cnpj("") is False
        assert validar_cnpj("1" * 13) is False
        assert validar_cnpj("1" * 15) is False

    def test_cnpj_sequencia_repetida(self):
        assert validar_cnpj("00000000000000") is False
        assert validar_cnpj("11111111111111") is False
        assert validar_cnpj("99999999999999") is False

    def test_cnpj_none(self):
        assert validar_cnpj(None) is False

    def test_formatar_cnpj_com_mascara(self):
        assert formatar_cnpj("11222333000181") == "11.222.333/0001-81"

    def test_formatar_cnpj_ja_formatado(self):
        assert formatar_cnpj("11.222.333/0001-81") == "11.222.333/0001-81"

    def test_formatar_cnpj_invalido_devolve_cru(self):
        # Não levanta; devolve o que recebeu (sem máscara)
        assert formatar_cnpj("123") == "123"


# ============================================================
# Bcrypt
# ============================================================


class TestBcrypt:
    """Hash e verificação de senha com bcrypt."""

    def test_hash_tem_60_caracteres(self):
        h = hash_senha("minhasenha")
        assert isinstance(h, bytes)
        assert len(h) == 60

    def test_hash_comeca_com_prefixo_bcrypt(self):
        h = hash_senha("qualquer")
        assert h.startswith(b"$2")

    def test_verificar_senha_correta(self):
        h = hash_senha("senha123")
        assert verificar_senha("senha123", h) is True

    def test_verificar_senha_errada(self):
        h = hash_senha("senha123")
        assert verificar_senha("outra", h) is False

    def test_hash_e_diferente_a_cada_vez(self):
        # Salt é aleatório; o mesmo plaintext gera hashes diferentes
        h1 = hash_senha("mesma")
        h2 = hash_senha("mesma")
        assert h1 != h2
        # Mas ambos validam
        assert verificar_senha("mesma", h1) is True
        assert verificar_senha("mesma", h2) is True

    def test_hash_senha_vazia_raise(self):
        with pytest.raises(ValueError):
            hash_senha("")

    def test_verificar_senha_vazia_retorna_false(self):
        h = hash_senha("valida")
        assert verificar_senha("", h) is False
        assert verificar_senha("valida", "") is False

    def test_verificar_senha_rejeita_texto_puro_legado(self):
        # Senhas antigas em texto puro não podem mais autenticar
        assert verificar_senha("qualquer", "senha_em_claro") is False
        assert verificar_senha("qualquer", "") is False

    def test_hash_suporta_senha_maior_que_72_bytes_cr03(self):
        """CR-03: bcrypt limita 72 bytes; o pre-normalizador SHA-256
        contorna isso. Senhas arbitrariamente longas devem funcionar.
        """
        senha_longa = "a" * 100  # 100 bytes, > 72
        h = hash_senha(senha_longa)
        assert verificar_senha(senha_longa, h) is True

    def test_hash_suporta_senha_com_acentos_cr03(self):
        """CR-03: senha com acentos e emoji (que estouram 72 bytes UTF-8)
        deve funcionar via pre-normalização.
        """
        senha = "🔒" * 50  # 200 bytes em UTF-8
        h = hash_senha(senha)
        assert verificar_senha(senha, h) is True

    def test_hash_suporta_senha_realista_cr03(self):
        """CR-03: cenário realista de senha forte com 80+ chars."""
        senha = "SenhaForte🔒ComMuitosEmojis🌟2024ParaSegurança123!"
        h = hash_senha(senha)
        assert verificar_senha(senha, h) is True
        assert verificar_senha(senha + "x", h) is False

    def test_verificar_senha_bytes_nao_explode_me11(self):
        """ME-11: passar bytes em vez de str não deve explodir
        com TypeError; deve decodificar e validar."""
        h = hash_senha("Abc123")
        assert verificar_senha(b"Abc123", h) is True
        assert verificar_senha(b"errada", h) is False

    def test_validar_senha_complexidade_aceita_bytes_me11(self):
        """ME-11: validar_senha_complexidade aceita bytes."""
        ok, _ = validar_senha_complexidade(b"Abc123")
        assert ok is True
        ok, _ = validar_senha_complexidade(b"fraca")
        assert ok is False
        # Não-str nem bytes
        ok, msg = validar_senha_complexidade(123)
        assert ok is False
        assert "string" in msg.lower()


# ============================================================
# Validação de complexidade de senha
# ============================================================


class TestSenhaComplexidade:
    """Regras de complexidade mínima no cadastro."""

    def test_aceita_senha_valida(self):
        ok, _ = validar_senha_complexidade("abc123")
        assert ok is True

    def test_aceita_senha_longa_valida(self):
        ok, _ = validar_senha_complexidade("MinhaSenhaForte2024!")
        assert ok is True

    def test_rejeita_vazia(self):
        ok, msg = validar_senha_complexidade("")
        assert ok is False
        assert "vazia" in msg.lower()

    def test_rejeita_muito_curta(self):
        ok, msg = validar_senha_complexidade("ab1")
        assert ok is False
        assert "6" in msg

    def test_rejeita_sem_letra(self):
        ok, msg = validar_senha_complexidade("123456")
        assert ok is False
        assert "letra" in msg.lower()

    def test_rejeita_sem_numero(self):
        ok, msg = validar_senha_complexidade("abcdef")
        assert ok is False
        assert "mero" in msg.lower() or "número" in msg.lower()

    def test_aceita_senha_com_caracteres_especiais(self):
        # Especiais são bonus, não obrigatórios
        ok, _ = validar_senha_complexidade("senha!1")
        assert ok is True
