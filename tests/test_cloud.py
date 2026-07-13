"""Testes do FlowLog Cloud v2.0.

Roda com SQLite em memória + httpx.AsyncClient.
Sem Postgres/MySQL. Cobre:
    - Auth (signup, login, refresh, me)
    - Produtos (CRUD + entrada + saida)
    - Multi-tenant (isolamento entre tenants)
    - Dashboard (KPIs)
"""

import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Forçar SQLite em memória antes de importar o app
os.environ["DB_HOST"] = "localhost"
os.environ["JWT_SECRET"] = "test-secret-for-pytest-only"

from cloud.config import settings  # noqa: E402
from cloud.database import Base, get_session  # noqa: E402
from cloud.main import app  # noqa: E402
from cloud.models import audit, fornecedor, historico, produto, tenant, user  # noqa: E402, F401

# Substitui URL por SQLite
settings.db_echo = False

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(autouse=True)
async def setup_db():
    """Cria tabelas e dropa antes/depois de cada teste."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ============================================================
# Health
# ============================================================


async def test_health(client):
    r = await client.get("/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["versao"] == "2.0.0"


# ============================================================
# Signup + Login
# ============================================================


async def test_signup_cria_tenant_e_user(client):
    r = await client.post(
        "/v1/auth/signup",
        json={
            "tenant_nome": "Empresa X",
            "admin_email": "admin@x.com",
            "admin_username": "admin",
            "admin_senha": "senha12345",
            "plano": "free",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["tenant_id"]
    assert body["user_id"]
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


async def test_signup_email_duplicado(client):
    payload = {
        "tenant_nome": "Empresa X",
        "admin_email": "dup@x.com",
        "admin_username": "admin",
        "admin_senha": "senha12345",
    }
    r1 = await client.post("/v1/auth/signup", json=payload)
    assert r1.status_code == 201
    r2 = await client.post(
        "/v1/auth/signup",
        json={**payload, "tenant_nome": "Empresa Y", "admin_username": "outro"},
    )
    assert r2.status_code == 409


async def test_login_credenciais_validas(client):
    await client.post(
        "/v1/auth/signup",
        json={
            "tenant_nome": "Empresa X",
            "admin_email": "user@x.com",
            "admin_username": "admin_x",
            "admin_senha": "senha12345",
        },
    )
    r = await client.post("/v1/auth/login", json={"email": "user@x.com", "senha": "senha12345"})
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"]
    assert body["user_id"]


async def test_login_senha_incorreta(client):
    await client.post(
        "/v1/auth/signup",
        json={
            "tenant_nome": "Empresa X",
            "admin_email": "user@x.com",
            "admin_username": "admin_x",
            "admin_senha": "senha12345",
        },
    )
    r = await client.post("/v1/auth/login", json={"email": "user@x.com", "senha": "errada"})
    assert r.status_code == 401


async def test_refresh_token(client):
    r1 = await client.post(
        "/v1/auth/signup",
        json={
            "tenant_nome": "Empresa X",
            "admin_email": "user@x.com",
            "admin_username": "admin_x",
            "admin_senha": "senha12345",
        },
    )
    refresh = r1.json()["refresh_token"]
    r2 = await client.post("/v1/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 200
    assert r2.json()["access_token"]


async def test_refresh_token_invalido(client):
    r = await client.post("/v1/auth/refresh", json={"refresh_token": "nao-eh-jwt"})
    assert r.status_code == 401


# ============================================================
# Me (autenticação)
# ============================================================


async def test_me_sem_token(client):
    r = await client.get("/v1/auth/me")
    assert r.status_code == 401


async def test_me_com_token(client):
    r1 = await client.post(
        "/v1/auth/signup",
        json={
            "tenant_nome": "Minha Empresa",
            "admin_email": "a@e.com",
            "admin_username": "admin_user",
            "admin_senha": "senha12345",
        },
    )
    token = r1.json()["access_token"]
    r2 = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    body = r2.json()
    assert body["nome"] == "Minha Empresa"
    assert body["plano"] == "free"


# ============================================================
# Produtos (CRUD)
# ============================================================


async def _signup(client) -> str:
    """Helper: cria tenant e retorna access token."""
    r = await client.post(
        "/v1/auth/signup",
        json={
            "tenant_nome": "Empresa P",
            "admin_email": f"a{os.urandom(4).hex()}@p.com",
            "admin_username": f"admin_{os.urandom(2).hex()}",
            "admin_senha": "senha12345",
        },
    )
    return r.json()["access_token"]


async def test_criar_produto(client):
    token = await _signup(client)
    r = await client.post(
        "/v1/produtos",
        headers={"Authorization": f"Bearer {token}"},
        json={"nome": "Notebook", "quantidade": 10, "preco_custo": 1500.0, "preco_venda": 2200.0},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["nome"] == "Notebook"
    assert body["quantidade"] == 10


async def test_listar_produtos(client):
    token = await _signup(client)
    h = {"Authorization": f"Bearer {token}"}
    for nome in ["Item A", "Item B", "Item C"]:
        await client.post("/v1/produtos", headers=h, json={"nome": nome})
    r = await client.get("/v1/produtos", headers=h)
    assert r.status_code == 200
    assert len(r.json()) == 3


async def test_buscar_produto(client):
    token = await _signup(client)
    h = {"Authorization": f"Bearer {token}"}
    r1 = await client.post("/v1/produtos", headers=h, json={"nome": "Mouse"})
    pid = r1.json()["id"]
    r2 = await client.get(f"/v1/produtos/{pid}", headers=h)
    assert r2.status_code == 200
    assert r2.json()["nome"] == "Mouse"


async def test_editar_produto(client):
    token = await _signup(client)
    h = {"Authorization": f"Bearer {token}"}
    r1 = await client.post("/v1/produtos", headers=h, json={"nome": "Velho"})
    pid = r1.json()["id"]
    r2 = await client.patch(
        f"/v1/produtos/{pid}", headers=h, json={"nome": "Novo", "preco_custo": 99.0}
    )
    assert r2.status_code == 200
    assert r2.json()["nome"] == "Novo"
    assert r2.json()["preco_custo"] == 99.0


# ============================================================
# Movimentações
# ============================================================


async def test_entrada_soma_estoque(client):
    token = await _signup(client)
    h = {"Authorization": f"Bearer {token}"}
    r1 = await client.post("/v1/produtos", headers=h, json={"nome": "X", "quantidade": 5})
    pid = r1.json()["id"]
    r2 = await client.post(f"/v1/produtos/{pid}/entrada", headers=h, json={"quantidade": 3})
    assert r2.status_code == 200
    assert r2.json()["qtd_anterior"] == 5
    assert r2.json()["qtd_nova"] == 8


async def test_saida_subtrai_estoque(client):
    token = await _signup(client)
    h = {"Authorization": f"Bearer {token}"}
    r1 = await client.post("/v1/produtos", headers=h, json={"nome": "X", "quantidade": 10})
    pid = r1.json()["id"]
    r2 = await client.post(f"/v1/produtos/{pid}/saida", headers=h, json={"quantidade": 4})
    assert r2.status_code == 200
    assert r2.json()["qtd_nova"] == 6


async def test_saida_sem_estoque(client):
    token = await _signup(client)
    h = {"Authorization": f"Bearer {token}"}
    r1 = await client.post("/v1/produtos", headers=h, json={"nome": "X", "quantidade": 2})
    pid = r1.json()["id"]
    r2 = await client.post(f"/v1/produtos/{pid}/saida", headers=h, json={"quantidade": 10})
    assert r2.status_code == 409
    assert "insuficiente" in r2.json()["detail"].lower()


async def test_movimentacao_quantidade_zero(client):
    token = await _signup(client)
    h = {"Authorization": f"Bearer {token}"}
    r1 = await client.post("/v1/produtos", headers=h, json={"nome": "X"})
    pid = r1.json()["id"]
    r2 = await client.post(f"/v1/produtos/{pid}/entrada", headers=h, json={"quantidade": 0})
    assert r2.status_code == 422  # Pydantic rejeita


# ============================================================
# Multi-tenant (isolamento)
# ============================================================


async def test_multi_tenant_isolamento(client):
    """Tenant B não vê produto do Tenant A."""
    token_a = await _signup(client)
    token_b = await _signup(client)
    h_a = {"Authorization": f"Bearer {token_a}"}
    h_b = {"Authorization": f"Bearer {token_b}"}

    # A cria produto
    r = await client.post("/v1/produtos", headers=h_a, json={"nome": "Secreto A"})
    pid_a = r.json()["id"]

    # B tenta acessar o produto de A
    r = await client.get(f"/v1/produtos/{pid_a}", headers=h_b)
    assert r.status_code == 404  # não vaza existência

    # B lista — não vê o produto de A
    r = await client.get("/v1/produtos", headers=h_b)
    assert len(r.json()) == 0

    # A lista — vê o próprio produto
    r = await client.get("/v1/produtos", headers=h_a)
    assert len(r.json()) == 1


async def test_multi_tenant_dashboard_isolado(client):
    token_a = await _signup(client)
    token_b = await _signup(client)
    h_a = {"Authorization": f"Bearer {token_a}"}
    h_b = {"Authorization": f"Bearer {token_b}"}

    # A tem 3 produtos, B tem 1
    for nome in ["A1", "A2", "A3"]:
        await client.post("/v1/produtos", headers=h_a, json={"nome": nome})
    await client.post("/v1/produtos", headers=h_b, json={"nome": "B1"})

    r_a = await client.get("/v1/dashboard/resumo", headers=h_a)
    r_b = await client.get("/v1/dashboard/resumo", headers=h_b)

    assert r_a.json()["total_produtos"] == 3
    assert r_b.json()["total_produtos"] == 1


# ============================================================
# Dashboard
# ============================================================


async def test_dashboard_resumo(client):
    token = await _signup(client)
    h = {"Authorization": f"Bearer {token}"}
    await client.post("/v1/produtos", headers=h, json={"nome": "X", "quantidade": 10, "alerta_minimo": 5})
    await client.post("/v1/produtos", headers=h, json={"nome": "Y", "quantidade": 2, "alerta_minimo": 5})
    r = await client.get("/v1/dashboard/resumo", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["total_produtos"] == 2
    assert body["total_quantidade_estoque"] == 12
    assert body["produtos_em_alerta"] == 1


# ============================================================
# Token inválido
# ============================================================


async def test_token_invalido(client):
    r = await client.get("/v1/produtos", headers={"Authorization": "Bearer lixo"})
    assert r.status_code == 401


async def test_token_garbage(client):
    r = await client.get("/v1/produtos", headers={"Authorization": "Bearer "})
    assert r.status_code == 401
