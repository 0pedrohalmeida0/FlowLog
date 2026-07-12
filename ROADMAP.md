# 🗺️ FlowLog — Roadmap

> Planejamento vivo do projeto. Atualizado conforme versões saem e o contexto muda.
> *Living planning document. Updated as versions ship and context evolves.*

> **Atualizado em 2026-07-12: virada estratégica para 3 SKUs** (Licença, Enterprise, Cloud).

---

## 🎯 Onde estamos hoje (julho de 2026)

| Versão | Estado | Entregue |
|--------|--------|----------|
| **v1.2** | ✅ Released | Bloqueio de conta, auto-logout, complexidade de senha, `.env.example` |
| **v1.3** | ✅ Released | Edição de produto, CSV import/export, backup via mysqldump, sugestão de compra |
| **v1.4** | ✅ Released | Repository + Service pattern, exceções custom, type hints, **2 QA passes** (36 bugs corrigidos) |

A base está sólida. O código atual reaproveita ~80% do que virá nos próximos SKUs: services, repositories, exceções, validações, CNPJ, bcrypt, CSV. A camada de apresentação (CLI) será substituída por web/REST no Cloud; tudo o que está por baixo é reutilizável.

---

## 🏢 A nova estratégia: 3 SKUs

A partir de agora, o FlowLog deixa de ser "um software instalável" e vira uma **família de produtos** com 3 pontos de entrada no mercado:

| SKU | Tipo | Onde roda | Quem opera | Modelo de receita |
|-----|------|-----------|------------|-------------------|
| **FlowLog Licença** | Software | Cliente (Windows) | Cliente | One-time ou anual |
| **FlowLog Enterprise** | Software + | Cliente (Windows/Linux) | Cliente | Anual (premium) |
| **FlowLog Cloud** | SaaS | Servidor (nós) | Nós | Mensal (recorrente) |

A ordem de execução é: **Licença → Enterprise → Cloud**. Cada SKU destrava o próximo em complexidade e em capacidade de receita recorrente.

---

## 🛣️ v1.5 — FlowLog Licença GA (4-6 semanas) 📦

**Tema:** empacotar tudo o que já existe num instalador Windows vendável. O software local é a porta de entrada do mercado e o que financia o desenvolvimento do Cloud.

### O que entra

- **`pyproject.toml`** (instalável como pacote: `pip install flowlog`).
- **PyInstaller** → executável único standalone (Windows + Linux .AppImage).
- **Inno Setup** → instalador `.exe` Windows com wizard (atalho no menu iniciar, desinstalador, ícone).
- **Setup wizard no primeiro start** — detecta/cria `.env`, testa conexão MySQL, roda `schema.sql`, cria admin user padrão (`admin/admin123`, força troca no primeiro login).
- **Auto-update via GitHub Releases** — checa nova versão no startup, prompt pro user baixar.
- **Localização** — strings em PT-BR + EN (i18n via `gettext`).
- **Documentação de venda** — README com screenshots, página de features, FAQ, "como instalar", "como migrar de outro sistema".
- **Política de licença** — free trial de 30 dias (com watermark no relatório), ativação por chave.

### Por que primeiro

É o caminho mais curto até receita. Cliente paga R$X uma vez → recebe instalador. Sem risco de churn (compra única). E financia o desenvolvimento do Cloud.

### Critério de pronto

- `pip install flowlog` funciona em Python 3.10+ limpo.
- Instalador `.exe` roda em Windows 10/11 sem Python pré-instalado.
- Setup wizard completa em < 3 minutos (instalação + schema + admin user).
- Tamanho do instalador ≤ 100 MB.
- Auto-update funciona para releases novos.
- Documentação de venda no GitHub README + pasta `docs/venda/`.

### Risco

🟠 **Médio.** PyInstaller é cheio de pegadinha (paths, hidden imports do `mysql-connector`). Inno Setup tem curva. Auto-update em desktop é frágil. Mas a base é Python, não tem nada de nativo — mitigável.

### Features por SKU (este release é só Licença)

- ✅ Tudo da v1.4 (cadastro, estoque, histórico, Curva ABC, CSV, backup)
- ❌ Multi-filial (Enterprise)
- ❌ API REST (Enterprise)
- ❌ Web (Cloud)

---

## 🏢 v1.6 — FlowLog Enterprise Beta (4-6 semanas) 🏗️

**Tema:** a mesma base de código da Licença, mas com **features premium** que justificam o ticket anual maior. On-premise, mas com esteroides.

### O que entra

- **Multi-filial / multi-CNPJ** — uma instalação, vários tenants via `empresa_id`. Cada query filtra por tenant. Schema novo: `empresas`, `usuarios_empresas` (N:N). Migração do schema v1.5 com script de migration.
- **RBAC granular por empresa** — usuário pode ser admin na Filial A e operador na Filial B. Decorator `@requer_nivel_empresa(empresa_id, nivel)`.
- **API REST local** (FastAPI) sob o mesmo processo: `/api/produtos`, `/api/movimentacoes`, `/api/relatorios`. **Não exposta à internet** — uso interno pra integração com ERP local.
- **Autenticação SSO/LDAP** — opcional, configurável no admin panel. Active Directory, OpenLDAP.
- **Audit log avançado** — `auditoria_acoes` separada do histórico de estoque. Registra: usuário, IP, user-agent, ação, payload. Retenção configurável (default 365 dias).
- **Dashboard de métricas web** (`/admin/metrics`) — Chart.js com: produtos mais vendidos, evolução de estoque, alertas críticos por mês, top fornecedores.
- **Relatórios premium** — projeção de compra (MRP simplificado), DRE por filial, fluxo de caixa, aging de estoque.
- **White-label** — logo, cores e nome do cliente no relatório exportado.
- **Suporte dedicado** (comercial, fora do software) — SLA 24h, canal direto.

### Por que segundo

A v1.5 prova que o produto funciona. A v1.6 faz ele falar com sistemas legados (ERP, BI) que o cliente B2B já tem. Quem tem ERP, paga mais — esse é o segmento que paga anual. A receita recorrente começa aqui (anual, não mensal ainda).

### Critério de pronto

- Multi-filial: cadastro de empresa, troca de contexto, isolamento de dados por tenant.
- API REST: 100% das rotas testadas, OpenAPI/Swagger UI em `/docs`.
- LDAP: opcional, configurável, testado contra OpenLDAP + Active Directory.
- Audit log: 1 ano de retenção padrão, configurável, exportável.
- Dashboard: 5+ gráficos, refresh em < 5s.
- White-label: PDF/CSV do relatório com logo do cliente.

### Risco

🔴 **Alto.** Mudança de schema é migração pesada. Multi-tenant exige refactor de TODA query existente (acrescentar `WHERE empresa_id = X` em todos os SELECTs). RBAC granular é fácil de fazer errado. API local exige cuidado com autenticação e rate limit.

### Features por SKU

- ✅ Tudo da Licença
- ➕ Multi-filial, RBAC por empresa, API REST local, LDAP, audit log avançado, dashboard, white-label
- ❌ Web (Cloud)

---

## 🌐 v2.0 — FlowLog Cloud MVP (8-12 semanas) ☁️

**Tema:** tirar o software do cliente e colocar na web. Multi-tenant real (vários clientes no mesmo banco). Receita recorrente mensal.

### O que entra

- **Backend FastAPI** — reaproveita services e repositories do v1.6. Migração para ORM opcional (SQLAlchemy) ou manter queries parametrizadas. Endpoints versionados (`/v1/...`).
- **Frontend web** (React ou Vue.js, a definir) — SPA com login, dashboard, CRUDs, relatórios, gráficos. Tema responsivo (desktop + tablet).
- **Multi-tenancy** — schema-per-tenant (PostgreSQL) **ou** row-level com `empresa_id` (MySQL). Decisão arquitetural crítica.
- **Auth web** — JWT com refresh token, "esqueci a senha" via e-mail, OAuth2 Google/Microsoft opcional.
- **Stripe (ou ASAAS pra BR)** — billing recorrente. Tiers: **Free** (1 user, 100 produtos), **Pro** (5 users, produtos ilimitados), **Business** (50 users, integrações).
- **E-mail transacional** — SendGrid ou AWS SES. Templates: "Bem-vindo", "Alerta de estoque", "Fatura disponível".
- **Infraestrutura** — Docker + docker-compose, CI/CD com GitHub Actions, deploy automatizado (Fly.io, Render ou DigitalOcean App Platform).
- **Painel admin global** (pra gente) — listar tenants, suspender conta, estender trial, ver MRR.
- **Onboarding self-service** — signup → escolha plano → 14 dias trial → cobrança.

### Por que terceiro

É o maior salto técnico (web do zero, multi-tenancy, billing). Faz sentido vir depois que a base local estiver sólida (v1.5 + v1.6). Receita recorrente mensal é o objetivo de longo prazo.

### Critério de pronto

- Backend serve 100 req/s com latência p95 < 200ms.
- Frontend tem fluxo completo: signup → login → cadastrar produto → dar entrada → ver histórico → exportar CSV.
- 1 tenant de teste roda isolado, dados não vazam pra outros tenants.
- Stripe cobra automaticamente todo dia 1º, falha de pagamento suspende conta após 3 dias.
- Deploy via `git push main` → ambiente de staging live em < 10 min.
- Painel admin mostra MRR, churn, tenants ativos.

### Risco

🔴 **Muito alto.** Web é um novo mundo (CI/CD, infra, segurança web, sessões em cookie vs JWT). Multi-tenancy tem 5 formas de fazer, todas com trade-offs. Billing é cheio de edge case (mudança de plano, proration, refund, failed payment). Reservar buffer de 50% no prazo.

### Stack proposta

- **Backend**: FastAPI + Pydantic + SQLAlchemy 2.0 (async) + Alembic migrations
- **DB**: PostgreSQL 15 (multi-tenant via `tenant_id` em cada row)
- **Frontend**: React 18 + Vite + TailwindCSS + shadcn/ui + React Query + Recharts
- **Auth**: FastAPI-Users ou Auth0 (decidir)
- **Billing**: Stripe (global) + ASAAS (Brasil)
- **E-mail**: Resend ou SendGrid
- **Infra**: Docker → Fly.io ou Render → Cloudflare CDN
- **Observabilidade**: Sentry (errors) + PostHog (product analytics) + Grafana Cloud (metrics)

### Features por SKU

- ✅ Tudo da Enterprise
- ➕ Web, multi-tenant, billing recorrente, signup self-service, e-mail transacional
- 🆕 Plano Free (vai competir com a Licença em funcionalidade, mas é web)

---

## 🚀 v2.1 — FlowLog Cloud GA (4-6 semanas) 🎯

**Tema:** tirar o "beta" do Cloud. Polimento, integrações que vendem, e a primeira campanha de marketing.

### O que entra

- **Integrações nativas** — webhook Zapier, conector Tiny ERP (BR), conector Bling (BR), Shopify stock sync.
- **API pública** — REST autenticada por API key (escopo read/read-write), rate limit por tier, OpenAPI/Swagger público em `developers.flowlog.app`.
- **Mobile-friendly PWA** — frontend vira Progressive Web App, instala no celular do gerente, push notifications de alerta.
- **White-label completo** (provedores de SaaS B2B) — subdomínio customizado (`estoque.empresa.com.br`), logo, cores.
- **Campos customizados por tenant** — admin pode criar colunas extras em `produtos` (ex: `ncm`, `peso_kg`, `localizacao_fisica`).
- **Importação avançada** — Excel (.xlsx), CSV, integração direta com NFe.
- **Marketing site** — `flowlog.app` com landing page, pricing, calculadora de ROI, blog, depoimentos.
- **Self-host opcional (Enterprise+)** — "quero Cloud, mas na minha infra" — vendemos o stack Docker.

### Por que quarto

Depois que o MVP tá rodando com 10-50 clientes, a gente sabe o que falta. As integrações são pull de demanda. White-label e PWA abrem novos segmentos (B2B2B, franquias).

### Critério de pronto

- 3+ integrações nativas publicadas e testadas.
- API pública estável, com 5+ integrações de terceiros construídas.
- PWA instalável, push de notificação funcionando.
- Marketing site no ar com calculadora de ROI.
- 100+ tenants ativos no Cloud.

### Risco

🟠 **Médio.** Não tem refactor grande. É adicionar features em cima de base madura. O risco é comercial (chutar pricing, tração).

---

## 🔮 v3.0 — IA & Automação (6-8 semanas) 🤖

**Tema:** usar o que o FlowLog coleta (movimentações, alertas, histórico) pra **prever e automatizar**.

### O que entra

- **Previsão de demanda** — Prophet ou ARIMA, rodando nos dados do tenant. "Vai precisar comprar 50 unidades do SKU X em 12 dias."
- **Detecção de anomalia** — "esse produto teve 3 saídas anormais essa semana, pode estar com problema de qualidade."
- **Compra automática (opcional)** — emite pedido de compra no ERP quando estoque <= ponto de pedido (Enterprise+Cloud).
- **Chatbot de consulta** — "quantas unidades do mouse sem fio tem em estoque?" via WhatsApp ou webchat (Cloud).
- **Insights diários** — resumo diário por e-mail/Slack ("3 produtos entraram em alerta, 2 fornecedores com lead time estourado, sugestão de compra X").
- **Recomendação de pricing** — "você vende teclado mecânico a R$150, similar no mercado é R$130-170, considere R$145" (Cloud Pro+).

### Por que último

IA exige volume de dados. Só faz sentido depois de ter N clientes com N meses de histórico. É também o diferencial competitivo mais forte pra justificar preço maior.

### Critério de pronto

- Previsão de demanda com MAPE < 30% (baseline honesto).
- Insights diários enviados automaticamente.
- 1 caso de uso de detecção de anomalia documentado (e-mail com explicação didática).
- Chatbot respondendo 70% das perguntas sem escalação pra humano.

### Risco

🟠 **Médio.** Modelos preditivos exigem dados limpos e em volume. O risco maior é prometer demais e entregar欠preciso. Mitigação: começar com "sugestão" (não decisão automática), o humano valida.

---

## 📊 Resumo de prazos

| Versão | SKU | Tema | Duração | Risco | Receita |
|--------|-----|------|---------|-------|---------|
| v1.5 | Licença | Empacotamento + venda local | 4-6 sem | 🟠 | One-time |
| v1.6 | Enterprise | Multi-filial + API + audit | 4-6 sem | 🔴 | Anual |
| v2.0 | Cloud MVP | Web + multi-tenant + billing | 8-12 sem | 🔴🔴 | Mensal |
| v2.1 | Cloud GA | Integrações + PWA + marketing | 4-6 sem | 🟠 | Mensal+ |
| v3.0 | IA | Previsão + automação | 6-8 sem | 🟠 | Upsell |

**Total até Cloud GA:** ~20-30 semanas (~5-7 meses). É o caminho pra ter receita recorrente.

---

## 🎯 Caminho crítico (caminho feliz)

```
v1.4d (atual) 
   ↓
v1.5 Licença GA  →  primeira receita (vendas pontuais)
   ↓
v1.6 Enterprise   →  receita anual (clientes B2B)
   ↓
v2.0 Cloud MVP    →  receita recorrente (SaaS)
   ↓
v2.1 Cloud GA     →  escala + marketing
   ↓
v3.0 IA           →  diferenciação + upsell
```

## 🎯 Caminho alternativo (paralelizar)

Se houver fôlego (dev júnior + dev sênior), dá pra paralelizar:

- **Time A (sênior)**: v1.5 (empacotamento) → v1.6 (Enterprise)
- **Time B (júnior + mentoria)**: prototipar Cloud em paralelo, validar stack

O risco de paralelizar é divergência de schema entre Licença e Cloud. Mitigação: **definir contrato da API primeiro** (v1.6 Enterprise), e o Cloud implementa o mesmo contrato. Quando migrar, é só trocar a UI.

---

## 🤔 Decisões pendentes (precisam de resposta)

1. **Pricing** — quanto cobrar por SKU/tier? (impacta diretamente o roadmap de features premium vs. core)
2. **Jurídico** — qual o CNPJ, regime tributário, modelo de contrato (assinatura digital)?
3. **Nome de domínio** — `flowlog.app` está disponível? (decide se é .com.br, .app, .com)
4. **Hospedagem Cloud inicial** — Fly.io vs Render vs DigitalOcean vs Hetzner (impacta custo e região)
5. **Banco de dados do Cloud** — PostgreSQL gerenciado (Supabase, Neon) ou self-hosted? (impacta custo recorrente)
6. **Pagamento** — Stripe global + ASAAS BR, ou só Stripe, ou só ASAAS?
7. **Suporte** — Discord, e-mail, ou chamado interno? (impacta ferramentas e processo)

---

## 💡 Princípios de decisão

- **Reaproveitar > Reescrever**: 80% do código v1.4d vira Cloud MVP.
- **Vender antes de terminar**: v1.5 deve poder ser vendido HOJE, mesmo que o Cloud não exista.
- **Receita diversificada**: Licença (pontual) + Enterprise (anual) + Cloud (mensal) reduz risco.
- **B2B primeiro, B2C depois**: pequenas e médias empresas têm LTV maior e churn menor que usuário individual.
- **Self-host opcional no futuro**: Enterprise que quiser virar Cloud particular, vendemos o stack Docker.

---

*Última atualização: 2026-07-12 (virada estratégica para 3 SKUs).*
*Próxima revisão: ao fim da v1.5.*
