# Como rodar o FlowLog Cloud (v2.0) local

Guia pra subir o backend + frontend + Postgres em dev.

## Opção A: Docker Compose (recomendado)

```bash
cd /workspace/FlowLog
docker compose -f docker-compose.cloud.yml up --build
```

Acessos:
- API:    http://localhost:8000
- Docs:   http://localhost:8000/docs
- Banco:  localhost:5432 (user/pass: flowlog/flowlog)

## Opção B: Manual (sem Docker)

### 1. Subir Postgres

```bash
docker run -d --name flowlog-pg \
  -e POSTGRES_USER=flowlog -e POSTGRES_PASSWORD=flowlog -e POSTGRES_DB=flowlog \
  -p 5432:5432 postgres:15-alpine
```

### 2. Backend (FastAPI)

```bash
cd /workspace/FlowLog
pip install -e '.[dev]'

# Variáveis de ambiente
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=flowlog
export DB_PASSWORD=flowlog
export DB_NAME=flowlog
export JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
export AMBIENTE=dev

# Roda
PYTHONPATH=. uvicorn cloud.main:app --reload --port 8000
```

Acessos:
- API:    http://localhost:8000
- Docs:   http://localhost:8000/docs

### 3. Frontend (React)

Em outra aba:

```bash
cd /workspace/FlowLog/src/cloud/frontend
npm install
npm run dev
```

Acesso: http://localhost:5173 (proxy automático pra `localhost:8000`)

---

## Primeiro uso

1. Abra http://localhost:5173
2. Clique em **Cadastre-se**
3. Preencha nome da empresa + admin (email/senha)
4. 14 dias trial, sem cartão
5. Você cai no Dashboard

## Testar a API direto

```bash
# 1. Signup
curl -X POST http://localhost:8000/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_nome": "Empresa Teste",
    "admin_email": "admin@empresa.com",
    "admin_username": "admin",
    "admin_senha": "senha12345",
    "plano": "free"
  }'

# (vai retornar access_token + refresh_token)

# 2. Listar produtos (autenticado)
curl http://localhost:8000/v1/produtos \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN"
```

## Multi-tenant na prática

O JWT carrega o `tenant_id`. Toda query a `produtos`, `fornecedores`, `historico_movimentacoes` etc. **filtra automaticamente** por esse `tenant_id`. Tentativa de acessar produto de outro tenant retorna 404 (não vaza existência).

Pra testar isolamento:

```bash
# 1. Crie 2 contas (Tenant A e Tenant B)
# 2. Crie um produto no Tenant A
# 3. Tente acessar o produto com o token do Tenant B
# → 404 Not Found
```

## Diferença vs Licença (v1.6)

| Aspecto | Licença (v1.6) | Cloud (v2.0) |
|---|---|---|
| Instalação | local (.exe) | web (browser) |
| Banco | MySQL local | PostgreSQL (Postgres multi-tenant) |
| Multi-filial | `empresa_id` (N:N) | `tenant_id` (row-level) |
| Auth | `fl_<u>_<n>_<sig>` | JWT Bearer + refresh |
| API | FastAPI local sob `/v1` | FastAPI Cloud sob `/v1` (mesmo path) |
| Billing | Licença HMAC 1x | Stripe/ASAAS recorrente |
| Mobile | não | PWA (v2.1) |
| White-label | `branding.json` | completo (v2.1) |

## Estrutura de pastas

```
src/cloud/
├── auth/         # JWT + bcrypt + dependencies
├── models/       # SQLAlchemy 2.0 (Tenant, User, Produto, ...)
├── schemas/      # Pydantic v2 (Signup, Login, Produto, ...)
├── routers/      # FastAPI routers (auth, produtos, dashboard)
├── billing/      # Stub de planos (Free/Pro/Business)
├── frontend/     # React 18 + Vite
├── config.py
├── database.py
├── main.py       # FastAPI app
└── __init__.py
```

## Próximos passos (v2.1)

- [ ] Stripe/ASAAS real (billing recorrente)
- [ ] E-mail transacional (SendGrid/Resend)
- [ ] PWA + mobile
- [ ] Integrações nativas (Tiny, Bling, Zapier)
- [ ] White-label completo pra revenda
- [ ] Painel admin global (MRR, churn, tenants)
- [ ] Marketing site `flowlog.app`
- [ ] SSO (Google, Microsoft)
- [ ] Logs centralizados (Sentry, PostHog)
- [ ] CI/CD no GitHub Actions
