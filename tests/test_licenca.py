"""Testes do sistema de licença: chave, trial, persistência."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from licenca import (
    EstadoLicenca,
    aplicar_watermark,
    ativar_licenca,
    carregar_estado,
    gerar_chave,
    inicializar_trial,
    status_licenca,
    validar_chave,
)


@pytest.fixture
def tmp_license_dir(tmp_path, monkeypatch):
    """Redireciona o diretório de licença pra tmp_path."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    # Windows usa APPDATA
    monkeypatch.setenv("APPDATA", str(tmp_path))
    return tmp_path


class TestGerarChave:
    def test_chave_formato_correto(self):
        chave = gerar_chave(validade_dias=365, cliente="Teste")
        partes = chave.split("-")
        # v1.5: 5 grupos de 5 (25 chars no total)
        assert len(partes) == 5
        assert all(len(g) == 5 for g in partes)
        assert chave.replace("-", "").isalnum()

    def test_chaves_sao_unicas(self):
        c1 = gerar_chave(validade_dias=365, cliente="A")
        c2 = gerar_chave(validade_dias=365, cliente="A")
        # Timestamp + nonce diferentes => chaves diferentes
        assert c1 != c2

    def test_chave_vitalicia(self):
        chave = gerar_chave(validade_dias=None, cliente="Vitalicio")
        info = validar_chave(chave)
        assert info is not None
        assert info["cliente_hash"] is not None
        assert info["expira_em"] is None


class TestValidarChave:
    def test_chave_valida(self):
        chave = gerar_chave(validade_dias=365, cliente="ACME LTDA")
        info = validar_chave(chave)
        assert info is not None
        assert info["cliente_hash"] is not None
        assert info["expira_em"] > datetime.now()

    def test_chave_vazia_invalida(self):
        assert validar_chave("") is None
        assert validar_chave("AAAA-BBBB-CCCC-DDDD-EEEE") is None  # HMAC errado

    def test_chave_malformada(self):
        assert validar_chave("não-é-chave") is None
        assert validar_chave("ABC") is None
        assert validar_chave("ABC-DEF") is None

    def test_chave_expirada(self):
        # Mock: simula chave cuja data de expiração está no passado.
        # Gera uma chave válida, depois força a expira_em no passado.

        chave = gerar_chave(validade_dias=365, cliente="Expirado")
        # Patch _unpack_payload pra retornar data passada
        with patch("licenca._unpack_payload") as mock_unpack:
            mock_unpack.return_value = {
                "product_id": "flowlog-v1",
                "cliente_hash": "abc",
                "emitida_em": datetime.now() - timedelta(days=400),
                "expira_em": datetime.now() - timedelta(days=30),
            }
            info = validar_chave(chave)
        assert info is None


class TestEstadoLicenca:
    def test_em_trial_quando_trial(self):
        agora = datetime.now()
        estado = EstadoLicenca(
            modo="trial",
            instalada_em=agora - timedelta(days=5),
            expira_em=agora + timedelta(days=25),
        )
        assert estado.em_trial() is True
        assert estado.trial_expirado() is False

    def test_trial_expirado(self):
        agora = datetime.now()
        estado = EstadoLicenca(
            modo="trial",
            instalada_em=agora - timedelta(days=40),
            expira_em=agora - timedelta(days=10),
        )
        assert estado.em_trial() is False
        assert estado.trial_expirado() is True

    def test_ativada_nao_em_trial(self):
        agora = datetime.now()
        estado = EstadoLicenca(
            modo="activated",
            instalada_em=agora - timedelta(days=100),
            expira_em=None,
            chave="AAAAA-BBBBB-CCCCC-DDDDD-EEEEE",
            ativa_em=agora - timedelta(days=70),
            cliente_hash="abc123",
        )
        assert estado.em_trial() is False
        assert estado.trial_expirado() is False

    def test_dias_restantes_trial(self):
        agora = datetime.now()
        estado = EstadoLicenca(
            modo="trial",
            instalada_em=agora,
            expira_em=agora + timedelta(days=10),
        )
        # 10 dias inteiros restantes
        assert estado.dias_restantes_trial() in (10, 11)

    def test_to_from_dict_roundtrip(self):
        agora = datetime.now()
        original = EstadoLicenca(
            modo="trial",
            instalada_em=agora,
            expira_em=agora + timedelta(days=30),
        )
        d = original.to_dict()
        reconstructed = EstadoLicenca.from_dict(d)
        assert reconstructed.modo == original.modo
        assert reconstructed.instalada_em == original.instalada_em
        assert reconstructed.expira_em == original.expira_em


class TestPersistencia:
    def test_inicializar_trial_cria_estado(self, tmp_license_dir):
        estado = inicializar_trial()
        assert estado.modo == "trial"
        assert estado.expira_em is not None
        # Idempotente: segunda chamada retorna o mesmo
        estado2 = inicializar_trial()
        assert estado.instalada_em == estado2.instalada_em

    def test_carregar_estado_inexistente(self, tmp_license_dir):
        assert carregar_estado() is None

    def test_status_licenca_cria_trial_se_necessario(self, tmp_license_dir):
        estado = status_licenca()
        assert estado.modo == "trial"


class TestAtivarLicenca:
    def test_ativar_com_sucesso(self, tmp_license_dir):
        inicializar_trial()
        chave = gerar_chave(validade_dias=365, cliente="ACME LTDA")
        novo = ativar_licenca(chave)
        assert novo.modo == "activated"
        # v1.5: cliente vira hash, não nome (privacidade)
        assert novo.cliente_hash is not None
        assert novo.chave == chave

    def test_ativar_chave_invalida_levanta_erro(self, tmp_license_dir):
        inicializar_trial()
        with pytest.raises(ValueError):
            ativar_licenca("CHAVE-INVALIDA-AQUI")


class TestWatermark:
    def test_watermark_em_trial(self, tmp_license_dir):
        inicializar_trial()
        texto = aplicar_watermark("Relatório de inventário")
        assert "FLOWLOG TRIAL" in texto
        assert "Relatório de inventário" in texto

    def test_watermark_apos_ativacao(self, tmp_license_dir):
        inicializar_trial()
        chave = gerar_chave(validade_dias=365, cliente="ACME")
        ativar_licenca(chave)
        texto = aplicar_watermark("Relatório de inventário")
        assert "FLOWLOG TRIAL" not in texto
        assert texto == "Relatório de inventário"
