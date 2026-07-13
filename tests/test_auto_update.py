"""Testes do auto_update: parsing de versão, comparação, detecção de update."""

import json
from unittest.mock import MagicMock, patch

import auto_update


class TestParseVersion:
    def test_v_prefix(self):
        assert auto_update._parse_version("v1.5.0") == (1, 5, 0)

    def test_sem_prefixo(self):
        assert auto_update._parse_version("1.5.0") == (1, 5, 0)

    def test_com_rc(self):
        # rc1 não vira parte numérica, fica só (1, 5, 0)
        assert auto_update._parse_version("v1.5.0-rc1") == (1, 5, 0)

    def test_com_4_niveis(self):
        # Permite calendar versioning (YYYY.MM.DD.X)
        assert auto_update._parse_version("2026.7.13.0") == (2026, 7, 13, 0)


class TestIsNewer:
    def test_patch_maior(self):
        assert auto_update._is_newer("v1.5.1", "1.5.0") is True
        assert auto_update._is_newer("v1.5.0", "1.5.1") is False

    def test_minor_maior(self):
        assert auto_update._is_newer("v2.0.0", "1.5.0") is True

    def test_mesma_versao(self):
        assert auto_update._is_newer("v1.5.0", "1.5.0") is False

    def test_versao_invalida(self):
        # Não crasha
        assert auto_update._is_newer("xyz", "1.0.0") is False


class TestChecarAtualizacao:
    def test_sem_update_quando_mesma_versao(self):
        fake_response = MagicMock()
        fake_response.read.return_value = json.dumps(
            {
                "tag_name": "v1.5.0",
                "html_url": "https://example.com",
                "body": "notes",
            }
        ).encode("utf-8")
        fake_response.__enter__ = lambda self: self
        fake_response.__exit__ = lambda self, *args: None

        with patch("urllib.request.urlopen", return_value=fake_response):
            info = auto_update.checar_atualizacao("1.5.0")
        assert info is None

    def test_com_update_quando_maior(self):
        fake_response = MagicMock()
        fake_response.read.return_value = json.dumps(
            {
                "tag_name": "v1.6.0",
                "html_url": "https://example.com/v1.6.0",
                "body": "Release notes",
                "published_at": "2026-08-01T00:00:00Z",
            }
        ).encode("utf-8")
        fake_response.__enter__ = lambda self: self
        fake_response.__exit__ = lambda self, *args: None

        with patch("urllib.request.urlopen", return_value=fake_response):
            info = auto_update.checar_atualizacao("1.5.0")
        assert info is not None
        assert info["version"] == "1.6.0"
        assert info["url"] == "https://example.com/v1.6.0"

    def test_falha_de_rede_retorna_none(self):
        import urllib.error

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            info = auto_update.checar_atualizacao("1.5.0")
        assert info is None

    def test_json_invalido_retorna_none(self):
        fake_response = MagicMock()
        fake_response.read.return_value = b"nao e json"
        fake_response.__enter__ = lambda self: self
        fake_response.__exit__ = lambda self, *args: None

        with patch("urllib.request.urlopen", return_value=fake_response):
            info = auto_update.checar_atualizacao("1.5.0")
        assert info is None
