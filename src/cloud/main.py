"""FlowLog Cloud — entry point (v2.0).

FastAPI app que serve:
    - REST API sob /v1
    - Frontend estático em /
    - OpenAPI/Swagger em /docs

Como rodar:
    # Dev (com hot-reload):
    uvicorn cloud.main:app --reload --port 8000

    # Produção (com Gunicorn ou uvicorn workers):
    uvicorn cloud.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from cloud.config import settings
from cloud.database import dispose_db, init_db
from cloud.routers import auth, dashboard, produtos

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown do app."""
    logger.info("FlowLog Cloud v%s iniciando (ambiente=%s)", settings.versao, settings.ambiente)
    if settings.ambiente == "dev":
        await init_db()  # dev: cria tabelas automaticamente
    yield
    await dispose_db()
    logger.info("FlowLog Cloud encerrado")


app = FastAPI(
    title="FlowLog Cloud API",
    description=(
        "API REST do FlowLog Cloud v2.0. Multi-tenant real, JWT auth, "
        "OpenAPI/Swagger em /docs."
    ),
    version=settings.versao,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/v1")
app.include_router(produtos.router, prefix="/v1")
app.include_router(dashboard.router, prefix="/v1")


@app.get("/v1/health", tags=["sistema"])
def health():
    """Health check simples."""
    return {
        "status": "ok",
        "versao": settings.versao,
        "ambiente": settings.ambiente,
    }


# ============================================================
# Entry point
# ============================================================


def main():  # pragma: no cover
    """Entry point: `python -m src.cloud.main` ou `flowlog-cloud`."""
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
