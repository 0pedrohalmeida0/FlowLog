"""FlowLog Cloud (v2.0) — pacote principal.

Stack:
    - FastAPI + Pydantic + SQLAlchemy 2.0 async
    - PostgreSQL 15
    - JWT auth
    - Multi-tenant row-level (tenant_id em cada row de negócio)
"""

__version__ = "2.0.0"
