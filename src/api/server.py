"""FlowLog API REST local (v1.6 — Licença + Premium).

Endpoints (todos sob /v1):
    GET    /v1/health                      — health check
    GET    /v1/empresas                    — lista empresas do usuário
    POST   /v1/empresas                    — cadastra empresa
    GET    /v1/produtos                    — lista produtos da empresa atual
    POST   /v1/produtos                    — cadastra produto
    GET    /v1/produtos/{id}               — busca produto
    PATCH  /v1/produtos/{id}               — edita produto
    POST   /v1/produtos/{id}/entrada       — entrada de estoque
    POST   /v1/produtos/{id}/saida         — saída de estoque
    GET    /v1/movimentacoes               — histórico (com filtros)
    GET    /v1/relatorios/curva-abc        — Curva ABC
    GET    /v1/relatorios/inventario       — inventário atual

Auth:
    Header `Authorization: Bearer fl_<token>`. Sem token = 401.

Multi-tenant:
    Header `X-FlowLog-Empresa: <id>` OU setado no login inicial.
    Toda query é filtrada por empresa_id (v1.6).

Como rodar:
    python -m src.api.server
    # ou
    flowlog-api
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from api.auth import gerar_token, validar_token
from audit import audit_acao_direta
from exceptions import (
    CNPJInvalidoError,
    EstoqueInsuficienteError,
    NotFoundError,
    ValidationError,
)
from logging_config import get_logger, setup_logging
from services import (
    EmpresaService,
    EstoqueService,
    ProdutoService,
)

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


# ============================================================
# Schemas Pydantic
# ============================================================


class HealthResponse(BaseModel):
    status: str
    versao: str
    db_ok: bool


class EmpresaCreate(BaseModel):
    cnpj: str = Field(..., description="CNPJ (com ou sem máscara)")
    razao_social: str
    nome_fantasia: str | None = None


class EmpresaOut(BaseModel):
    id: int
    cnpj: str
    razao_social: str
    nome_fantasia: str | None
    ativa: bool


class ProdutoCreate(BaseModel):
    nome: str
    quantidade: int = 0
    preco_custo: float = 0.0
    fornecedor_cnpj: str | None = None
    alerta_minimo: int | None = None


class ProdutoOut(BaseModel):
    id: int
    empresa_id: int
    nome: str
    quantidade: int
    preco_custo: float
    fornecedor_id: int | None
    alerta_minimo: int | None


class ProdutoEdit(BaseModel):
    nome: str | None = None
    preco_custo: float | None = None
    alerta_minimo: int | None = None


class MovimentacaoIn(BaseModel):
    quantidade: int = Field(..., gt=0)


class MovimentacaoOut(BaseModel):
    produto_id: int
    nome: str
    qtd_anterior: int
    qtd_nova: int


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None


# ============================================================
# App + dependency
# ============================================================

VERSAO = "1.6.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("FlowLog API v%s iniciada", VERSAO)
    yield
    logger.info("FlowLog API encerrada")


app = FastAPI(
    title="FlowLog Licença API",
    description="API REST local do FlowLog Licença v1.6 (multi-filial, audit log).",
    version=VERSAO,
    lifespan=lifespan,
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_empresa: str | None = Header(None, alias="X-FlowLog-Empresa"),
):
    """Valida token Bearer e seleciona empresa (se header presente)."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ausente. Use Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    info = validar_token(credentials.credentials)
    if info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Se header X-FlowLog-Empresa presente, seleciona a empresa
    if x_empresa is not None:
        try:
            empresa_id = int(x_empresa)
            EmpresaService().selecionar_empresa(empresa_id)
        except (NotFoundError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Sem acesso à empresa {x_empresa}.",
            ) from exc
    else:
        # Auto-seleciona se o user só tem 1 empresa
        EmpresaService().auto_selecionar_se_unica()

    return info


# ============================================================
# Health
# ============================================================


@app.get("/v1/health", response_model=HealthResponse, tags=["sistema"])
def health():
    """Health check simples."""
    from database import Database

    try:
        db = Database()
        conn = db.connect()
        db_ok = conn is not None
        if conn:
            conn.close()
    except Exception:
        db_ok = False
    return HealthResponse(status="ok", versao=VERSAO, db_ok=db_ok)


# ============================================================
# Empresas
# ============================================================


@app.get("/v1/empresas", response_model=list[EmpresaOut], tags=["empresas"])
def listar_empresas(user: dict = Depends(get_current_user)):
    """Lista empresas do usuário logado."""
    try:
        svc = EmpresaService()
        empresas = svc.empresas_do_usuario(user["id"])
        return [EmpresaOut(**e) for e in empresas]
    except Exception as e:
        logger.exception("Erro em GET /v1/empresas")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post(
    "/v1/empresas",
    response_model=EmpresaOut,
    status_code=status.HTTP_201_CREATED,
    tags=["empresas"],
)
def criar_empresa(
    body: EmpresaCreate,
    user: dict = Depends(get_current_user),
):
    """Cadastra uma nova empresa (filial)."""
    if user is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    try:
        svc = EmpresaService()
        novo_id = svc.cadastrar(
            cnpj=body.cnpj,
            razao_social=body.razao_social,
            nome_fantasia=body.nome_fantasia,
        )
        audit_acao_direta(
            acao="CREATE",
            recurso="empresa",
            recurso_id=novo_id,
            payload={"cnpj": body.cnpj, "razao_social": body.razao_social},
        )
        # Retorna a empresa criada
        empresas = svc.listar()
        emp = next((e for e in empresas if e["id"] == novo_id), None)
        if not emp:
            raise HTTPException(status_code=500, detail="Empresa criada mas não encontrada")
        return EmpresaOut(**emp)
    except CNPJInvalidoError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.exception("Erro em POST /v1/empresas")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ============================================================
# Produtos
# ============================================================


@app.get("/v1/produtos", response_model=list[ProdutoOut], tags=["produtos"])
def listar_produtos(user: dict = Depends(get_current_user)):
    """Lista produtos da empresa atual (multi-tenant)."""
    try:
        produtos = ProdutoService().listar_todos()
        return [ProdutoOut(**p) for p in produtos]
    except Exception as e:
        logger.exception("Erro em GET /v1/produtos")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post(
    "/v1/produtos",
    response_model=ProdutoOut,
    status_code=status.HTTP_201_CREATED,
    tags=["produtos"],
)
def criar_produto(
    body: ProdutoCreate,
    user: dict = Depends(get_current_user),
):
    """Cadastra um produto na empresa atual."""
    try:
        novo_id = ProdutoService().cadastrar(
            nome=body.nome,
            quantidade=body.quantidade,
            preco_custo=body.preco_custo,
            fornecedor_cnpj=body.fornecedor_cnpj or "",
            alerta_minimo=body.alerta_minimo,
        )
        audit_acao_direta(
            acao="CREATE",
            recurso="produto",
            recurso_id=novo_id,
            payload={"nome": body.nome, "quantidade": body.quantidade},
        )
        prod = ProdutoService().buscar(novo_id)
        return ProdutoOut(**prod)
    except (CNPJInvalidoError, ValidationError) as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.exception("Erro em POST /v1/produtos")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/v1/produtos/{produto_id}", response_model=ProdutoOut, tags=["produtos"])
def buscar_produto(
    produto_id: int,
    user: dict = Depends(get_current_user),
):
    try:
        prod = ProdutoService().buscar(produto_id)
        if not prod:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        return ProdutoOut(**prod)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro em GET /v1/produtos/%d", produto_id)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.patch("/v1/produtos/{produto_id}", tags=["produtos"])
def editar_produto(
    produto_id: int,
    body: ProdutoEdit,
    user: dict = Depends(get_current_user),
):
    try:
        svc = ProdutoService()
        resultado = svc.editar(
            produto_id,
            {k: v for k, v in body.model_dump().items() if v is not None},
        )
        audit_acao_direta(
            acao="UPDATE",
            recurso="produto",
            recurso_id=produto_id,
            payload=body.model_dump(exclude_none=True),
        )
        return {"ok": True, "snapshot_antes": resultado["snapshot_antes"]}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.exception("Erro em PATCH /v1/produtos/%d", produto_id)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post(
    "/v1/produtos/{produto_id}/entrada",
    response_model=MovimentacaoOut,
    tags=["movimentacoes"],
)
def registrar_entrada(
    produto_id: int,
    body: MovimentacaoIn,
    user: dict = Depends(get_current_user),
):
    try:
        resultado = EstoqueService().registrar_entrada(produto_id, body.quantidade)
        audit_acao_direta(
            acao="ENTRADA",
            recurso="produto",
            recurso_id=produto_id,
            payload={"quantidade": body.quantidade},
        )
        return MovimentacaoOut(**resultado)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.exception("Erro em POST entrada")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post(
    "/v1/produtos/{produto_id}/saida",
    response_model=MovimentacaoOut,
    tags=["movimentacoes"],
)
def registrar_saida(
    produto_id: int,
    body: MovimentacaoIn,
    user: dict = Depends(get_current_user),
):
    try:
        resultado = EstoqueService().registrar_saida(produto_id, body.quantidade)
        audit_acao_direta(
            acao="SAIDA",
            recurso="produto",
            recurso_id=produto_id,
            payload={"quantidade": body.quantidade},
        )
        return MovimentacaoOut(**resultado)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except EstoqueInsuficienteError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.exception("Erro em POST saida")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ============================================================
# Movimentações / Relatórios
# ============================================================


@app.get("/v1/movimentacoes", tags=["movimentacoes"])
def listar_movimentacoes(
    tipo: str | None = None,
    limite: int = 200,
    user: dict = Depends(get_current_user),
):
    """Lista histórico de movimentações (filtro opcional: ENTRADA/SAIDA)."""
    try:
        from database import Database

        db = Database()
        conn = db.connect()
        if not conn:
            raise HTTPException(status_code=503, detail="DB indisponível")
        try:
            cur = conn.cursor(dictionary=True)
            sql = (
                "SELECT h.id, h.produto_id, p.nome AS produto, h.tipo, h.quantidade, "
                "       h.data_movimentacao, "
                "       COALESCE(u.username, '(sistema)') AS usuario "
                "FROM historico_movimentacoes h "
                "JOIN produtos p ON h.produto_id = p.id "
                "LEFT JOIN usuarios u ON h.usuario_id = u.id "
                "WHERE h.empresa_id = %s "
            )
            params = []
            from session import empresa_atual

            params.append(empresa_atual())
            if tipo:
                sql += " AND UPPER(h.tipo) = %s"
                params.append(tipo.upper())
            sql += " ORDER BY h.data_movimentacao DESC LIMIT %s"
            params.append(limite)
            cur.execute(sql, tuple(params))
            return cur.fetchall()
        finally:
            if conn.is_connected():
                conn.close()
    except Exception as e:
        logger.exception("Erro em GET /v1/movimentacoes")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ============================================================
# CLI helpers
# ============================================================


def main():  # pragma: no cover
    """Entry point: `python -m src.api.server [port] [--gerar-token USER]`."""
    import argparse

    parser = argparse.ArgumentParser(description="FlowLog API server")
    parser.add_argument("--port", type=int, default=8000, help="Porta (default 8000)")
    parser.add_argument("--host", default="127.0.0.1", help="Host (default localhost only)")
    parser.add_argument("--gerar-token", metavar="USERNAME", help="Gera um token Bearer")
    args = parser.parse_args()

    if args.gerar_token:
        token = gerar_token(args.gerar_token)
        print(f"Token para usuário '{args.gerar_token}':")
        print(f"  {token}")
        print()
        print("Use no header: Authorization: Bearer <token>")
        return 0

    try:
        import uvicorn
    except ImportError:
        print("❌ uvicorn não instalado. Rode: pip install uvicorn")
        return 1

    print(f"🚀 FlowLog API v{VERSAO} em http://{args.host}:{args.port}")
    print(f"   Swagger UI: http://{args.host}:{args.port}/docs")
    print("   ⚠️  NÃO exponha à internet — API local only.")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    import sys as _sys

    _sys.exit(main())
