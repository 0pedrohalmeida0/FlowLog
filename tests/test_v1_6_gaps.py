"""Testes pra módulos v1.6 que ficaram com cobertura baixa."""

from unittest.mock import MagicMock, patch

import pytest


# ============================================================
# EmpresaRepository
# ============================================================


def test_empresa_repository_instancia():
    from src.repositories.empresa_repository import EmpresaRepository

    repo = EmpresaRepository({"host": "x", "user": "y"})
    assert repo is not None
    assert repo._TABLE == "empresas"


def test_empresa_repository_buscar_por_cnpj():
    from src.repositories.empresa_repository import EmpresaRepository

    with patch.object(EmpresaRepository, "_connect") as mock_conn:
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {"id": 1, "cnpj": "123", "razao_social": "X"}
        mock_conn.return_value.cursor.return_value = mock_cur

        repo = EmpresaRepository({})
        result = repo.buscar_por_cnpj("123")
        assert result == {"id": 1, "cnpj": "123", "razao_social": "X"}


def test_empresa_repository_buscar_por_cnpj_none():
    from src.repositories.empresa_repository import EmpresaRepository

    with patch.object(EmpresaRepository, "_connect") as mock_conn:
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = None
        mock_conn.return_value.cursor.return_value = mock_cur

        repo = EmpresaRepository({})
        assert repo.buscar_por_cnpj("999") is None


def test_empresa_repository_listar_ativas():
    from src.repositories.empresa_repository import EmpresaRepository

    with patch.object(EmpresaRepository, "_connect") as mock_conn:
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [{"id": 1}, {"id": 2}]
        mock_conn.return_value.cursor.return_value = mock_cur

        repo = EmpresaRepository({})
        result = repo.listar(apenas_ativas=True)
        assert len(result) == 2


def test_empresa_repository_listar_todas():
    from src.repositories.empresa_repository import EmpresaRepository

    with patch.object(EmpresaRepository, "_connect") as mock_conn:
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = []
        mock_conn.return_value.cursor.return_value = mock_cur

        repo = EmpresaRepository({})
        result = repo.listar(apenas_ativas=False)
        assert result == []


# ============================================================
# AuditoriaRepository
# ============================================================


def test_auditoria_repository_instancia():
    from src.repositories.auditoria_repository import AuditoriaRepository

    repo = AuditoriaRepository({})
    assert repo is not None
    assert repo._TABLE == "auditoria_acoes"


def test_auditoria_repository_registrar():
    from src.repositories.auditoria_repository import AuditoriaRepository

    repo = AuditoriaRepository({})
    assert hasattr(repo, "registrar")
    assert hasattr(repo, "listar")


# ============================================================
# EmpresaService
# ============================================================


def test_empresa_service_instancia():
    from src.services.empresa_service import EmpresaService

    repo = MagicMock()
    service = EmpresaService(repo)
    assert service is not None


def test_empresa_service_listar():
    from src.services.empresa_service import EmpresaService

    repo = MagicMock()
    repo.listar.return_value = [{"id": 1}]
    service = EmpresaService(repo)
    result = service.listar()
    assert len(result) == 1


def test_empresa_service_desativar_reativar():
    from src.services.empresa_service import EmpresaService

    repo = MagicMock()
    service = EmpresaService(repo)
    service.desativar(1)
    service.reativar(1)


def test_empresa_service_usuarios():
    from src.services.empresa_service import EmpresaService

    repo = MagicMock()
    service = EmpresaService(repo)
    service.empresas_do_usuario(1)
    service.adicionar_usuario(1, 2, 3)
    service.remover_usuario(1, 2)


# ============================================================
# UsuarioService
# ============================================================


def test_usuario_service_instancia():
    from src.services.usuario_service import UsuarioService

    repo = MagicMock()
    service = UsuarioService(repo)
    assert service is not None


def test_usuario_service_cadastrar():
    from src.services.usuario_service import UsuarioService

    repo = MagicMock()
    repo.criar.return_value = 1
    service = UsuarioService(repo)
    result = service.cadastrar(username="user", senha="senha12345", nivel_acesso=3)
    assert result is not None


# ============================================================
# Cloud billing + auth (sem DB)
# ============================================================


def test_cloud_billing_plans_free():
    from cloud.billing.plans import info_plano
    from cloud.models import Plano

    info = info_plano(Plano.FREE)
    assert info.nome == "Free"
    assert info.max_usuarios == 1
    assert info.max_produtos == 100
    assert info.preco_mensal_brl == 0.0


def test_cloud_billing_plans_pro():
    from cloud.billing.plans import info_plano
    from cloud.models import Plano

    info = info_plano(Plano.PRO)
    assert info.preco_mensal_brl == 99.0
    assert info.max_usuarios == 5
    assert info.max_produtos is None


def test_cloud_billing_plans_business():
    from cloud.billing.plans import info_plano
    from cloud.models import Plano

    info = info_plano(Plano.BUSINESS)
    assert info.max_usuarios == 50


def test_cloud_password_hash_e_verify():
    from cloud.auth.password import hash_password, verify_password

    h = hash_password("senha12345")
    assert h.startswith("$2b$")
    assert verify_password("senha12345", h)
    assert not verify_password("errada", h)
    assert not verify_password("senha12345", "")
    assert not verify_password("", h)


def test_cloud_jwt_access_roundtrip():
    from cloud.auth.jwt import criar_access_token, decodificar_token

    token = criar_access_token("user-1", "tenant-1", "a@b.com")
    payload = decodificar_token(token)
    assert payload["sub"] == "user-1"
    assert payload["tenant_id"] == "tenant-1"
    assert payload["email"] == "a@b.com"
    assert payload["type"] == "access"


def test_cloud_jwt_access_com_extras():
    from cloud.auth.jwt import criar_access_token, decodificar_token

    token = criar_access_token("u", "t", "e", extra={"nivel": "admin"})
    payload = decodificar_token(token)
    assert payload["nivel"] == "admin"


def test_cloud_jwt_refresh_roundtrip():
    from cloud.auth.jwt import criar_refresh_token, decodificar_token

    token = criar_refresh_token("user-1")
    payload = decodificar_token(token)
    assert payload["sub"] == "user-1"
    assert payload["type"] == "refresh"
    assert "jti" in payload


def test_cloud_jwt_invalido():
    from cloud.auth.jwt import decodificar_token

    assert decodificar_token("lixo") is None
    assert decodificar_token("") is None
    assert decodificar_token("a.b.c") is None


def test_cloud_settings_defaults():
    from cloud.config import Settings

    s = Settings()
    assert s.versao == "2.0.0"
    assert s.jwt_algoritmo == "HS256"
    assert s.bcrypt_rounds >= 10
    assert s.cors_origins
    assert "http://localhost:5173" in s.cors_origins


def test_cloud_settings_database_urls():
    from cloud.config import Settings

    s = Settings(db_host="db.local", db_port=5433, db_user="u", db_password="p", db_name="n")
    assert "postgresql+asyncpg" in s.database_url_async
    assert "db.local" in s.database_url_async
    assert "postgresql+psycopg2" in s.database_url_sync
