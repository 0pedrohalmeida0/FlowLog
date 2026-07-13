"""FlowLog Cloud — entry point (v2.1)."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from cloud.config import settings
from cloud.database import dispose_db, init_db
from cloud.observability.sentry import init_sentry
from cloud.routers import admin, auth, billing, branding, dashboard, produtos

logger = logging.getLogger(__name__)

# Sentry: ativa se SENTRY_DSN estiver setado (no-op caso contrário)
init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown do app."""
    logger.info("FlowLog Cloud v%s iniciando (ambiente=%s)", settings.versao, settings.ambiente)
    if settings.ambiente == "dev":
        await init_db()

    # Cria super admin seed se configurado
    if settings.super_admin_email and settings.super_admin_senha:
        from sqlalchemy import select
        from cloud.auth.password import hash_password
        from cloud.models import NivelAcesso, User
        from cloud.database import session_scope

        async with session_scope() as session:
            result = await session.execute(
                select(User).where(User.email == settings.super_admin_email)
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                # Cria tenant "FlowLog Ops" + user super admin
                from cloud.models import Tenant
                from datetime import datetime, timezone, timedelta
                tenant = Tenant(
                    nome="FlowLog Ops",
                    plano="business",  # qualquer; super admin ignora
                    trial_expira_em=None,
                    ativo=True,
                )
                session.add(tenant)
                await session.flush()
                user = User(
                    tenant_id=tenant.id,
                    email=settings.super_admin_email,
                    username="admin",
                    senha_hash=hash_password(settings.super_admin_senha),
                    nivel_acesso=NivelAcesso.ADMIN,
                    super_admin=True,
                    ativo=True,
                )
                session.add(user)
                logger.info("✅ Super admin criado: %s", settings.super_admin_email)
            elif not existing.super_admin:
                existing.super_admin = True
                logger.info("✅ User %s promovido a super admin", settings.super_admin_email)

    yield
    await dispose_db()
    logger.info("FlowLog Cloud encerrado")


app = FastAPI(
    title="FlowLog Cloud API",
    description=(
        "API REST do FlowLog Cloud v2.1. Multi-tenant, JWT, white-label, "
        "billing manual, Google SSO, painel admin global. "
        "OpenAPI/Swagger em /docs."
    ),
    version=settings.versao,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers v2.1
app.include_router(auth.router, prefix="/v1")
app.include_router(produtos.router, prefix="/v1")
app.include_router(dashboard.router, prefix="/v1")
app.include_router(billing.router, prefix="/v1")
app.include_router(branding.router, prefix="/v1")
app.include_router(admin.router, prefix="/v1")


@app.get("/v1/health", tags=["sistema"])
def health():
    return {
        "status": "ok",
        "versao": settings.versao,
        "ambiente": settings.ambiente,
    }


def main():  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="FlowLog Cloud server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true", help="Hot-reload (dev)")
    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError:
        print("❌ uvicorn não instalado. Rode: pip install uvicorn")
        return 1

    print(f"☁️  FlowLog Cloud v{settings.versao} em http://{args.host}:{args.port}")
    print("   Swagger UI: http://{}:{}/docs".format(args.host, args.port))
    uvicorn.run(
        "cloud.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info" if settings.ambiente == "prod" else "debug",
    )
    return 0


if __name__ == "__main__":
    import sys as _sys

    _sys.exit(main())
