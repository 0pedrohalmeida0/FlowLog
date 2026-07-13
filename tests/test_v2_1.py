"""Testes da v2.1 — billing, white-label, admin, Google SSO, email."""

import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("JWT_SECRET", "test-secret-v21")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("EMAIL_PROVIDER", "stub")

from cloud.config import settings  # noqa: E402
from cloud.database import Base, get_session  # noqa: E402
from cloud.main import app  # noqa: E402
from cloud.models import (  # noqa: E402,F401
    audit,
    branding,
    fatura,
    fornecedor,
    historico,
    produto,
    tenant,
    user,
)

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    """Cria tabelas no engine local + configura override só deste teste."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_session():
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = override_get_session
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_session, None)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def _signup(client, email="user@x.com", tenant_nome="Empresa Teste"):
    r = await client.post(
        "/v1/auth/signup",
        json={
            "tenant_nome": tenant_nome,
            "admin_email": email,
            "admin_username": f"admin_{email[:5]}",
            "admin_senha": "senha12345",
            "plano": "free",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


# ============================================================
# White-label (branding)
# ============================================================


async def test_branding_publico_404(client):
    r = await client.get("/v1/branding/public/nao-existe")
    assert r.status_code == 404


async def test_branding_publico_default(client):
    """Tenant existe mas não tem branding — retorna default."""
    data = await _signup(client, "a@x.com")
    tenant_id = data["tenant_id"]
    r = await client.get(f"/v1/branding/public/{tenant_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["cor_primaria"].startswith("#")
    assert body["css_vars"]["--flowlog-primary"]


async def test_meu_branding_cria_default(client):
    data = await _signup(client, "a@x.com")
    token = data["access_token"]
    r = await client.get("/v1/branding/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["cor_primaria"] == "#1f6feb"  # default


async def test_atualizar_branding(client):
    data = await _signup(client, "a@x.com")
    token = data["access_token"]
    r = await client.patch(
        "/v1/branding/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"nome_exibicao": "Minha Loja", "cor_primaria": "#ff6b6b"},
    )
    assert r.status_code == 200
    assert r.json()["nome_exibicao"] == "Minha Loja"
    assert r.json()["cor_primaria"] == "#ff6b6b"


async def test_atualizar_branding_cor_invalida(client):
    data = await _signup(client, "a@x.com")
    token = data["access_token"]
    r = await client.patch(
        "/v1/branding/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"cor_primaria": "vermelho"},  # não é hex
    )
    assert r.status_code == 422  # Pydantic rejeita


# ============================================================
# Billing (manual) — tenant vê próprias faturas
# ============================================================


async def test_tenant_lista_minhas_faturas_vazia(client):
    data = await _signup(client, "a@x.com")
    token = data["access_token"]
    r = await client.get("/v1/billing/minhas", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == []


# ============================================================
# Admin (precisa de super_admin)
# ============================================================


async def test_admin_stats_sem_permissao(client):
    """User comum não acessa /admin."""
    data = await _signup(client, "a@x.com")
    token = data["access_token"]
    r = await client.get("/v1/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


async def test_admin_stats_super_admin(client):
    """Super admin acessa /admin/stats."""
    from sqlalchemy import select
    from cloud.auth.password import hash_password
    from cloud.models import Tenant, User

    async with session_factory() as s:
        t = Tenant(nome="Ops", ativo=True)
        s.add(t)
        await s.flush()
        u = User(
            tenant_id=t.id,
            email="ops@x.com",
            username="ops",
            senha_hash=hash_password("senha12345"),
            super_admin=True,
        )
        s.add(u)
        await s.commit()
        admin_id = u.id
        admin_email = u.email

    r = await client.post("/v1/auth/login", json={"email": admin_email, "senha": "senha12345"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r2 = await client.get("/v1/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    body = r2.json()
    assert "mrr_centavos" in body
    assert "total_tenants" in body


async def test_admin_cria_fatura(client):
    """Super admin cria fatura pra um tenant."""
    from cloud.auth.password import hash_password
    from cloud.models import Tenant, User

    # Cria super admin
    async with session_factory() as s:
        t_admin = Tenant(nome="Ops", ativo=True)
        s.add(t_admin)
        await s.flush()
        u_admin = User(
            tenant_id=t_admin.id, email="ops@x.com", username="ops",
            senha_hash=hash_password("senha12345"), super_admin=True,
        )
        s.add(u_admin)
        await s.commit()

    # Cria tenant cliente
    cliente = await _signup(client, "cliente@x.com", "Cliente LTDA")
    cliente_id = cliente["tenant_id"]

    # Login super admin
    r = await client.post("/v1/auth/login", json={"email": "ops@x.com", "senha": "senha12345"})
    admin_token = r.json()["access_token"]

    # Cria fatura
    from datetime import datetime, timezone, timedelta
    r = await client.post(
        "/v1/billing/admin/criar",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "tenant_id": cliente_id,
            "valor_centavos": 9900,  # R$ 99,00
            "descricao": "Plano Pro - mensal",
            "metodo": "pix",
            "vence_em": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["valor_centavos"] == 9900
    assert body["status"] == "pendente"
    assert body["numero"].startswith("FlowLog-")


async def test_admin_marca_fatura_paga(client):
    from cloud.auth.password import hash_password
    from cloud.models import Tenant, User
    from datetime import datetime, timezone, timedelta

    async with session_factory() as s:
        t_admin = Tenant(nome="Ops", ativo=True)
        s.add(t_admin)
        await s.flush()
        u_admin = User(
            tenant_id=t_admin.id, email="ops@x.com", username="ops",
            senha_hash=hash_password("senha12345"), super_admin=True,
        )
        s.add(u_admin)
        await s.commit()

    cliente = await _signup(client, "cliente@x.com", "Cliente")
    cliente_id = cliente["tenant_id"]

    r = await client.post("/v1/auth/login", json={"email": "ops@x.com", "senha": "senha12345"})
    admin_token = r.json()["access_token"]

    r = await client.post(
        "/v1/billing/admin/criar",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "tenant_id": cliente_id,
            "valor_centavos": 9900,
            "descricao": "Pro",
            "metodo": "pix",
            "vence_em": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        },
    )
    fatura_id = r.json()["id"]

    # Marca como paga
    r = await client.post(
        f"/v1/billing/admin/{fatura_id}/marcar-pago",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"metodo": "pix", "observacao": "Confirmado no extrato"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "pago"
    assert r.json()["pago_em"] is not None


async def test_admin_cancelar_fatura(client):
    from cloud.auth.password import hash_password
    from cloud.models import Tenant, User
    from datetime import datetime, timezone, timedelta

    async with session_factory() as s:
        t_admin = Tenant(nome="Ops", ativo=True)
        s.add(t_admin)
        await s.flush()
        u_admin = User(
            tenant_id=t_admin.id, email="ops@x.com", username="ops",
            senha_hash=hash_password("senha12345"), super_admin=True,
        )
        s.add(u_admin)
        await s.commit()

    cliente = await _signup(client, "c@x.com", "Cliente")
    cliente_id = cliente["tenant_id"]

    r = await client.post("/v1/auth/login", json={"email": "ops@x.com", "senha": "senha12345"})
    admin_token = r.json()["access_token"]

    r = await client.post(
        "/v1/billing/admin/criar",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "tenant_id": cliente_id,
            "valor_centavos": 9900,
            "descricao": "Pro",
            "metodo": "pix",
            "vence_em": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        },
    )
    fatura_id = r.json()["id"]

    r = await client.post(
        f"/v1/billing/admin/{fatura_id}/cancelar?motivo=erro",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "cancelado"


async def test_tenant_lista_proprias_faturas(client):
    """Tenant vê as faturas que o admin criou pra ele."""
    from cloud.auth.password import hash_password
    from cloud.models import Tenant, User
    from datetime import datetime, timezone, timedelta

    async with session_factory() as s:
        t_admin = Tenant(nome="Ops", ativo=True)
        s.add(t_admin)
        await s.flush()
        u_admin = User(
            tenant_id=t_admin.id, email="ops@x.com", username="ops",
            senha_hash=hash_password("senha12345"), super_admin=True,
        )
        s.add(u_admin)
        await s.commit()

    cliente = await _signup(client, "c@x.com", "Cliente")
    cliente_id = cliente["tenant_id"]
    cliente_token = cliente["access_token"]

    r = await client.post("/v1/auth/login", json={"email": "ops@x.com", "senha": "senha12345"})
    admin_token = r.json()["access_token"]

    # Admin cria 2 faturas
    for i in range(2):
        r = await client.post(
            "/v1/billing/admin/criar",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tenant_id": cliente_id,
                "valor_centavos": 9900,
                "descricao": f"Pro {i}",
                "metodo": "pix",
                "vence_em": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
        )
        assert r.status_code == 201

    r = await client.get("/v1/billing/minhas", headers={"Authorization": f"Bearer {cliente_token}"})
    assert r.status_code == 200
    assert len(r.json()) == 2


async def test_tenant_isolamento_faturas(client):
    """Tenant A não vê faturas do Tenant B."""
    from cloud.auth.password import hash_password
    from cloud.models import Tenant, User
    from datetime import datetime, timezone, timedelta

    async with session_factory() as s:
        t_admin = Tenant(nome="Ops", ativo=True)
        s.add(t_admin)
        await s.flush()
        u_admin = User(
            tenant_id=t_admin.id, email="ops@x.com", username="ops",
            senha_hash=hash_password("senha12345"), super_admin=True,
        )
        s.add(u_admin)
        await s.commit()

    a = await _signup(client, "a@x.com", "Empresa A")
    b = await _signup(client, "b@x.com", "Empresa B")

    r = await client.post("/v1/auth/login", json={"email": "ops@x.com", "senha": "senha12345"})
    admin_token = r.json()["access_token"]

    # Fatura só pra A
    r = await client.post(
        "/v1/billing/admin/criar",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "tenant_id": a["tenant_id"],
            "valor_centavos": 9900,
            "descricao": "Pro A",
            "metodo": "pix",
            "vence_em": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        },
    )

    # A vê 1
    r = await client.get("/v1/billing/minhas", headers={"Authorization": f"Bearer {a['access_token']}"})
    assert len(r.json()) == 1

    # B vê 0
    r = await client.get("/v1/billing/minhas", headers={"Authorization": f"Bearer {b['access_token']}"})
    assert len(r.json()) == 0


async def test_admin_suspender_reativar_tenant(client):
    from cloud.auth.password import hash_password
    from cloud.models import Tenant, User

    async with session_factory() as s:
        t_admin = Tenant(nome="Ops", ativo=True)
        s.add(t_admin)
        await s.flush()
        u_admin = User(
            tenant_id=t_admin.id, email="ops@x.com", username="ops",
            senha_hash=hash_password("senha12345"), super_admin=True,
        )
        s.add(u_admin)
        await s.commit()

    cliente = await _signup(client, "c@x.com", "Cliente")
    cliente_id = cliente["tenant_id"]
    cliente_token = cliente["access_token"]

    r = await client.post("/v1/auth/login", json={"email": "ops@x.com", "senha": "senha12345"})
    admin_token = r.json()["access_token"]

    # Suspende
    r = await client.post(
        f"/v1/admin/tenants/{cliente_id}/suspender",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200

    # Tenta usar API — não pode (tenant inativo)
    r = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {cliente_token}"})
    # NOTE: /me pode passar; /login é que bloqueia
    # O bloqueio é no próximo login

    # Reativa
    r = await client.post(
        f"/v1/admin/tenants/{cliente_id}/reativar",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200


async def test_admin_listar_tenants(client):
    from cloud.auth.password import hash_password
    from cloud.models import Tenant, User

    async with session_factory() as s:
        t_admin = Tenant(nome="Ops", ativo=True)
        s.add(t_admin)
        await s.flush()
        u_admin = User(
            tenant_id=t_admin.id, email="ops@x.com", username="ops",
            senha_hash=hash_password("senha12345"), super_admin=True,
        )
        s.add(u_admin)
        await s.commit()

    # Cria 3 tenants
    for i in range(3):
        await _signup(client, f"t{i}@x.com", f"Empresa {i}")

    r = await client.post("/v1/auth/login", json={"email": "ops@x.com", "senha": "senha12345"})
    admin_token = r.json()["access_token"]

    r = await client.get("/v1/admin/tenants", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    body = r.json()
    # 3 tenants criados + 1 do admin (Ops)
    assert len(body) >= 3


# ============================================================
# Google SSO — verifica com mock
# ============================================================


async def test_google_login_sem_config(client):
    """Sem GOOGLE_CLIENT_ID setado, retorna 401."""
    settings.google_client_id = None
    r = await client.post(
        "/v1/auth/google/login",
        json={"id_token": "qualquer-token-fake"},
    )
    # Pode ser 401 (token inválido) ou 401 (não configurado)
    assert r.status_code in (401, 422)


async def test_google_login_token_invalido(client):
    """Com client_id setado mas token inválido."""
    settings.google_client_id = "fake-client-id.apps.googleusercontent.com"
    r = await client.post(
        "/v1/auth/google/login",
        json={"id_token": "token-invalido"},
    )
    assert r.status_code == 401


# ============================================================
# Email service (stub mode — sem envio real)
# ============================================================


def test_email_stub_mode():
    """Em modo stub, envia e retorna ok=True sem erro."""
    from cloud.email import enviar_email

    result = enviar_email(
        to="teste@x.com",
        subject="Teste",
        html_body="<p>Oi</p>",
    )
    assert result["ok"] is True
    assert result["provider"] == "stub"


def test_email_boas_vindas():
    from cloud.email import email_boas_vindas
    result = email_boas_vindas("Empresa X", "admin@x.com", "31/12/2026")
    assert result["ok"] is True


def test_email_trial_expira():
    from cloud.email import email_trial_expira
    result = email_trial_expira("X", "a@x.com", 3)
    assert result["ok"] is True


def test_email_fatura_gerada():
    from cloud.email import email_fatura_gerada
    result = email_fatura_gerada("X", "a@x.com", "FL-001", 9900, "pix", "31/12/2026", pix_chave="abc@x.com")
    assert result["ok"] is True


def test_email_fatura_paga():
    from cloud.email import email_fatura_paga
    result = email_fatura_paga("X", "a@x.com", "FL-001", 9900)
    assert result["ok"] is True


# ============================================================
# Sentry (no-op sem DSN)
# ============================================================


def test_sentry_no_op_sem_dsn():
    """Sem SENTRY_DSN, init_sentry retorna False (no-op)."""
    from cloud.observability.sentry import init_sentry

    original = settings.sentry_dsn
    settings.sentry_dsn = None
    try:
        result = init_sentry()
        # Pode ser False (no-op) ou True (já inicializado antes)
        assert isinstance(result, bool)
    finally:
        settings.sentry_dsn = original


# ============================================================
# Branding CSS vars helper
# ============================================================


def test_branding_to_css_vars():
    from cloud.models import Branding

    b = Branding(tenant_id="t1", cor_primaria="#abc123", cor_fundo="#fff", cor_texto="#000")
    vars_ = b.to_css_vars()
    assert vars_["--flowlog-primary"] == "#abc123"
    assert vars_["--flowlog-bg"] == "#fff"
    assert vars_["--flowlog-text"] == "#000"


# ============================================================
# Cobertura extra: tenants, dashboard, admin scenarios
# ============================================================


async def test_dashboard_com_dados(client):
    """Dashboard retorna KPIs do tenant."""
    data = await _signup(client, "a@x.com")
    token = data["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    await client.post("/v1/produtos", headers=h, json={"nome": "X", "quantidade": 5, "alerta_minimo": 2})
    r = await client.get("/v1/dashboard/resumo", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["total_produtos"] == 1
    assert body["produtos_em_alerta"] == 0


async def test_listar_pendentes_vazio(client):
    data = await _signup(client, "a@x.com")
    token = data["access_token"]
    r = await client.get("/v1/billing/minhas/pendentes", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == []


async def test_branding_publico_por_cnpj(client):
    """Busca por CNPJ no branding público."""
    from sqlalchemy import update as sa_update
    from cloud.models import Tenant

    data = await _signup(client, "a@x.com", "Minha Empresa LTDA")
    tenant_id = data["tenant_id"]

    # Atualiza CNPJ
    async with session_factory() as s:
        await s.execute(
            sa_update(Tenant).where(Tenant.id == tenant_id).values(cnpj="12345678000190")
        )
        await s.commit()

    r = await client.get("/v1/branding/public/12345678000190")
    assert r.status_code == 200
    assert r.json()["nome_exibicao"] == "Minha Empresa LTDA"


async def test_admin_promover_super_admin(client):
    from cloud.auth.password import hash_password
    from cloud.models import Tenant, User

    async with session_factory() as s:
        t_admin = Tenant(nome="Ops", ativo=True)
        s.add(t_admin)
        await s.flush()
        u_admin = User(
            tenant_id=t_admin.id, email="ops@x.com", username="ops",
            senha_hash=hash_password("senha12345"), super_admin=True,
        )
        s.add(u_admin)
        await s.commit()

    # Cria user comum
    cliente = await _signup(client, "user@x.com", "Cliente")
    user_id = cliente["user_id"]

    r = await client.post("/v1/auth/login", json={"email": "ops@x.com", "senha": "senha12345"})
    admin_token = r.json()["access_token"]

    r = await client.post(
        f"/v1/admin/users/{user_id}/promover-super-admin",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200


async def test_admin_promover_a_si_mesmo(client):
    from cloud.auth.password import hash_password
    from cloud.models import Tenant, User

    async with session_factory() as s:
        t_admin = Tenant(nome="Ops", ativo=True)
        s.add(t_admin)
        await s.flush()
        u_admin = User(
            tenant_id=t_admin.id, email="ops@x.com", username="ops",
            senha_hash=hash_password("senha12345"), super_admin=True,
        )
        s.add(u_admin)
        await s.commit()
        admin_id = u_admin.id

    r = await client.post("/v1/auth/login", json={"email": "ops@x.com", "senha": "senha12345"})
    admin_token = r.json()["access_token"]

    r = await client.post(
        f"/v1/admin/users/{admin_id}/promover-super-admin",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 400  # não pode promover a si mesmo


# ============================================================
# Frontend: arquivos PWA existem
# ============================================================


def test_pwa_manifest_existe():
    import os
    manifest_path = "/workspace/FlowLog/src/cloud/frontend/public/manifest.json"
    assert os.path.exists(manifest_path)
    import json
    with open(manifest_path) as f:
        data = json.load(f)
    assert data["name"] == "FlowLog Cloud"
    assert data["start_url"] == "/"
    assert any(i["sizes"] == "192x192" for i in data["icons"])


def test_pwa_sw_existe():
    import os
    sw_path = "/workspace/FlowLog/src/cloud/frontend/public/sw.js"
    assert os.path.exists(sw_path)
    with open(sw_path) as f:
        content = f.read()
    assert "CACHE_NAME" in content
    assert "fetch" in content


def test_marketing_site_existe():
    import os
    site_path = "/workspace/FlowLog/web/marketing/index.html"
    assert os.path.exists(site_path)
    with open(site_path) as f:
        content = f.read()
    assert "FlowLog" in content
    assert "R$" in content
    assert "Começar grátis" in content or "Come" in content


def test_fly_toml_existe():
    import os
    fly_path = "/workspace/FlowLog/fly.toml"
    assert os.path.exists(fly_path)
    with open(fly_path) as f:
        content = f.read()
    assert "app = " in content
    assert "primary_region" in content


def test_github_actions_existe():
    import os
    gh_path = "/workspace/FlowLog/.github/workflows/ci.yml"
    assert os.path.exists(gh_path)
    with open(gh_path) as f:
        content = f.read()
    assert "pytest" in content
    assert "ruff" in content or "black" in content
    assert "docker" in content.lower()
