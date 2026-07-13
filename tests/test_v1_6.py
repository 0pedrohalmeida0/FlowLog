"""Testes da v1.6 — multi-filial, audit log, API auth, branding."""

from unittest.mock import MagicMock, patch

import audit
import branding
import session
from api import auth as api_auth

# ============================================================
# Multi-filial: session
# ============================================================


class TestSessionMultiFilial:
    def setup_method(self):
        session.logout()

    def teardown_method(self):
        session.logout()

    def test_login_inicializa_empresa_como_none(self):
        session.login(1, "u", 2)
        assert session.empresa_atual() is None
        assert session.nivel_empresa_atual() is None

    def test_setar_empresa_atual(self):
        session.login(1, "u", 2)
        session.setar_empresa_atual(42, 3)
        assert session.empresa_atual() == 42
        assert session.nivel_empresa_atual() == 3

    def test_limpar_empresa_atual(self):
        session.login(1, "u", 2)
        session.setar_empresa_atual(42, 3)
        session.limpar_empresa_atual()
        assert session.empresa_atual() is None
        assert session.nivel_empresa_atual() is None

    def test_login_com_ip_e_user_agent(self):
        session.login(1, "u", 2, ip="10.0.0.1", user_agent="Mozilla/5.0")
        assert session.ip_atual() == "10.0.0.1"
        assert session.user_agent_atual() == "Mozilla/5.0"

    def test_setar_contexto_auditoria(self):
        session.login(1, "u", 2)
        session.setar_contexto_auditoria(ip="192.168.1.1", user_agent="curl/8.0")
        assert session.ip_atual() == "192.168.1.1"
        assert session.user_agent_atual() == "curl/8.0"


# ============================================================
# Decorator @requer_nivel_empresa
# ============================================================


class TestRequerNivelEmpresa:
    def setup_method(self):
        session.logout()

    def teardown_method(self):
        session.logout()

    def test_sem_empresa_selecionada(self, capsys):
        from auth import requer_nivel_empresa

        @requer_nivel_empresa(2)
        def func():
            return "OK"

        session.login(1, "u", 2)
        result = func()
        assert result is None
        captured = capsys.readouterr()
        assert "Nenhuma filial" in captured.out

    def test_nivel_insuficiente(self, capsys):
        from auth import requer_nivel_empresa

        @requer_nivel_empresa(3)
        def func():
            return "OK"

        session.login(1, "u", 2)
        session.setar_empresa_atual(42, 1)  # nível 1, requer 3
        result = func()
        assert result is None
        captured = capsys.readouterr()
        assert "Acesso Negado" in captured.out

    def test_nivel_suficiente(self):
        from auth import requer_nivel_empresa

        @requer_nivel_empresa(2)
        def func():
            return "OK"

        session.login(1, "u", 2)
        session.setar_empresa_atual(42, 3)
        assert func() == "OK"


# ============================================================
# Decorator @audit
# ============================================================


class TestAuditDecorator:
    def test_audit_acao_direta_nao_levanta_erro(self):
        # Mock: simulamos falha de DB — audit NÃO pode quebrar
        with patch("database.Database") as mock_db:
            mock_db.return_value.connect.return_value = None
            # Não deve levantar exceção
            audit.audit_acao_direta(acao="LOGIN", recurso="usuario", payload={"username": "x"})

    def test_audit_decorator_preserva_retorno(self):
        @audit.audit(acao="TEST", recurso="thing")
        def minha_func(x, y):
            return x + y

        # Não levanta mesmo se audit falhar
        with patch("audit.AuditoriaRepository") as mock_repo:
            mock_repo.return_value.registrar.side_effect = Exception("DB fail")
            assert minha_func(2, 3) == 5


# ============================================================
# API: auth (token)
# ============================================================


class TestApiAuth:
    def test_gerar_token_formato(self):
        token = api_auth.gerar_token("alice")
        assert token.startswith("fl_alice_")
        partes = token.split("_")
        assert len(partes) == 4  # fl, username, nonce, sig

    def test_validar_token_invalido(self):
        assert api_auth.validar_token("token-invalido") is None
        assert api_auth.validar_token("") is None
        assert api_auth.validar_token("fl_a_b") is None  # formato errado

    def test_validar_token_valido(self):
        # Gera e valida
        token = api_auth.gerar_token("alice")
        # Mock: validar_token tenta carregar user do DB
        with patch("database.Database") as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {"id": 1, "nivel_acesso": 2}
            mock_conn.cursor.return_value = mock_cursor
            mock_conn.is_connected.return_value = True
            mock_db.return_value.connect.return_value = mock_conn

            info = api_auth.validar_token(token)
            assert info is not None
            assert info["username"] == "alice"
            # Sessão foi carregada
            assert session.usuario_id_atual() == 1

    def teardown_method(self):
        session.logout()


# ============================================================
# Branding
# ============================================================


class TestBranding:
    def test_defaults_quando_sem_arquivo(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        monkeypatch.setenv("APPDATA", str(tmp_path))
        branding.carregar_branding()
        b = branding.carregar_branding()
        assert b["empresa_display"] == "FlowLog"
        assert b["cor_primaria"] == "#1f6feb"

    def test_salvar_e_carregar(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        monkeypatch.setenv("APPDATA", str(tmp_path))
        branding.salvar_branding(
            {
                "empresa_display": "ACME LTDA",
                "cor_primaria": "#FF0000",
                "relatorio_rodape": "Confidencial",
            }
        )
        b = branding.carregar_branding()
        assert b["empresa_display"] == "ACME LTDA"
        assert b["cor_primaria"] == "#FF0000"
        assert b["relatorio_rodape"] == "Confidencial"

    def test_aplicar_rodape_com_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        monkeypatch.setenv("APPDATA", str(tmp_path))
        branding.salvar_branding({"relatorio_rodape": "Confidencial"})
        resultado = branding.aplicar_rodape("Relatório de vendas")
        assert "Confidencial" in resultado
        assert "Relatório de vendas" in resultado

    def test_aplicar_rodape_sem_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        monkeypatch.setenv("APPDATA", str(tmp_path))
        texto = branding.aplicar_rodape("Limpo")
        assert texto == "Limpo"
