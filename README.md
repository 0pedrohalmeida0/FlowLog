# FlowLog - Gestão de Inventário

<p align="center">
  <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python" />
  <img src="https://img.shields.io/badge/mysql-%23000f.svg?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL" />
  <img src="https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=ffdd33" alt="Git" />
  <img src="https://img.shields.io/badge/tests-123%20passing-brightgreen?style=for-the-badge" alt="Tests" />
  <img src="https://img.shields.io/badge/coverage-82%25-brightgreen?style=for-the-badge" alt="Coverage" />
</p>

> **Versão atual:** v1.4c (QA patch: 29 correções de segurança/integridade). Veja `CHANGELOG.md` para o histórico.

## 🇺🇸 English Version

FlowLog is a robust inventory control system developed in Python and integrated with a MySQL database. Focused on logistical efficiency, the system automates stock tracking, balance validations, and movement auditing directly through the terminal.

### Current Features (v1.4c)

* **Role-Based Access Control (RBAC):** Three-tier hierarchical security system (Operator, Manager, IT Admin) with secure authentication (bcrypt, arbitrary length) and restricted action permissions.
* **Account Lockout & Auto-Logout:** After 5 failed login attempts the account is blocked for 15 minutes; sessions expire after 30 minutes of inactivity (configurable).
* **Centralized Main Menu:** Intuitive terminal interface with a single entry point (`main.py`) that wires all feature modules. Handlers wrapped in try/except so a bug in one feature doesn't kill the app.
* **Product & Supplier Management:** Interactive registration, physical inventory listing (paginated), supplier-specific product filtering with automated CNPJ formatting and validation.
* **Smart Inbound & Outbound Logistics:** Stock entries and pull-outs using strictly ID-based tracking, with `SELECT ... FOR UPDATE` to prevent lost-update in concurrent edits and automatic balance verification to prevent negative stock. Every movement is logged.
* **Dynamic Movement Auditing (Logs):** Paginated, filterable tracking of every transaction (Entries, Exits) with case-insensitive SQL `JOIN`s for analytical auditing. Date format includes year.
* **Edit History Audit Trail (v1.3a):** Snapshot of the product before and after each edit (JSON in `produtos_historico_edicoes`).
* **Critical Stock Alert + Purchase Suggestions:** Notification on startup for items at or below their configured minimum, with automatic purchase quantity suggestions.
* **CSV Import/Export (v1.3b → v1.4c hardened):** Bulk import (with validation, 50 MB file-size cap, **CSV-injection sanitization** — CVE-2014-3524, and supplier dedup so duplicate CNPJs in the same CSV don't break the transaction) and export of inventory/history/Curva ABC to CSV (UTF-8 with BOM, Excel-friendly).
* **Backup/Restore (v1.3c → v1.4c hardened):** `mysqldump`/`mysql` integration with retention policy. **MySQL password is passed via env var, never via command line** — fix for the previous version that exposed the password in `ps aux`.
* **ABC Curve Report (Inventory Turnover):** Strategic BI tool using SQL window functions to rank products by outbound volume, with float-safe classification thresholds.
* **Robust Architecture (v1.4a+):** Layered design with custom exception hierarchy, repositories (encapsulated SQL), and services (business logic) — fully testable with mocks, no MySQL required.
* **Continuous Integration:** 123 tests passing in CI (GitHub Actions), ruff + black + coverage fail-under=70%.
* **Data Security:** Environment variables (`.env`) for credentials, bcrypt for passwords (pre-normalized with SHA-256 to support arbitrary length), strict defense against *SQL Injection* and *CSV Injection* (CVE-2014-3524). MySQL driver errors are sanitized before logging.

### Technologies Used
* **Language:** Python 3.x
* **Database:** MySQL 5.7+ / 8.x
* **Connectivity:** `mysql-connector-python` (with connection pooling)
* **Hashing:** `bcrypt` + `hashlib` (SHA-256 pre-normalization)
* **Testing:** `pytest` (123 tests, 82% coverage on testable modules)
* **Linting/Formatting:** `ruff` + `black`
* **Environment Configuration:** `python-dotenv`

### Quick Start
```bash
# 1. Configure credentials
cp .env.example .env
# edit .env with your MySQL user/password

# 2. Initialize the database (run once)
mysql -u root -p < schema.sql

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python src/main.py
```

### Project Structure
```
FlowLog/
├── src/                  # Application code
│   ├── main.py           # Entry point + menu
│   ├── database.py       # MySQL pool
│   ├── auth.py           # RBAC decorator
│   ├── session.py        # In-memory session
│   ├── exceptions.py     # Domain exception hierarchy
│   ├── repositories/     # SQL access (one per entity)
│   ├── services/         # Business logic
│   └── *.py              # Feature modules (thin)
├── tests/                # pytest suite (123 tests)
├── schema.sql            # Database schema
├── migrations/           # Version upgrades
├── scripts/              # Standalone utilities
├── .env.example          # Configuration template
├── CHANGELOG.md          # Release notes
└── QA_REPORT.md          # Quality audit (v1.4b)
```

---

## 🇧🇷 Versão em Português

O FlowLog é um sistema de controle de estoque robusto desenvolvido em Python com integração ao banco de dados MySQL. Focado em eficiência logística, o sistema automatiza o rastreio de mercadorias, validações de saldo e auditoria de movimentações diretamente pelo terminal.

### Funcionalidades Atuais (v1.4c)

* **Controle de Acesso Hierárquico (RBAC):** Sistema de segurança em três níveis (Operador, Gerência, Admin TI) com autenticação bcrypt (qualquer tamanho de senha) e bloqueio de telas por permissão de usuário.
* **Bloqueio de Conta e Auto-Logout:** Após 5 falhas de login a conta é bloqueada por 15 minutos; sessões expiram após 30 minutos de inatividade (configurável).
* **Menu Principal Centralizado:** Interface intuitiva via terminal com ponto único de entrada (`main.py`) que conecta todos os módulos de feature. Handlers embrulhados em try/except para que um bug num módulo não derrube o app.
* **Gestão de Produtos e Fornecedores:** Cadastro interativo, listagem física (paginada), filtro de produtos por fornecedor com formatação e validação automatizada de CNPJ.
* **Logística Inteligente de Entrada e Saída:** Recebimentos e baixas com `SELECT ... FOR UPDATE` para evitar lost-update em edições concorrentes e verificação matemática para impedir saldo negativo. Cada movimentação é registrada.
* **Auditoria Dinâmica de Movimentações (Logs):** Rastreamento paginado e filtrável de todas as transações (Entradas, Saídas) com `JOIN`s SQL *case-insensitive*. Formato de data inclui o ano.
* **Trilha de Auditoria de Edições (v1.3a):** Snapshot do produto antes e depois de cada edição (JSON em `produtos_historico_edicoes`).
* **Alerta de Estoque Crítico + Sugestões de Compra:** Notificação na inicialização para itens no mínimo configurado, com sugestão automática de quantidade a pedir.
* **Importação/Exportação CSV (v1.3b → v1.4c endurecido):** Import em massa (com validação, limite de 50 MB, **sanitização contra CSV injection** — CVE-2014-3524, e dedup de fornecedores para CNPJs repetidos no mesmo CSV) e exportação para CSV (UTF-8 com BOM).
* **Backup/Restauração (v1.3c → v1.4c endurecido):** Integração com `mysqldump`/`mysql` com política de retenção. **A senha do MySQL é passada via variável de ambiente, nunca na linha de comando** — correção da versão anterior que expunha a senha em `ps aux`.
* **Relatório de Curva ABC (Giro de Estoque):** Ferramenta estratégica de BI usando window functions SQL com classificação A/B/C protegida contra imprecisão de float.
* **Arquitetura Robusta (v1.4a+):** Design em camadas com hierarquia de exceções customizada, repositories (SQL encapsulado) e services (lógica de negócio) — totalmente testáveis com mocks, sem MySQL.
* **Integração Contínua:** 123 testes passando em CI (GitHub Actions), ruff + black + cobertura mínima 70%.
* **Segurança de Dados:** Variáveis de ambiente (`.env`) para credenciais, bcrypt para senhas (pré-normalizadas com SHA-256 para aceitar qualquer tamanho), proteção rigorosa contra *SQL Injection* e *CSV Injection* (CVE-2014-3524). Erros do driver MySQL são sanitizados antes de logar.

### Tecnologias Utilizadas
* **Linguagem:** Python 3.x
* **Banco de Dados:** MySQL 5.7+ / 8.x
* **Conectividade:** `mysql-connector-python` (com pool de conexões)
* **Hashing:** `bcrypt` + `hashlib` (SHA-256 pré-normalização)
* **Testes:** `pytest` (123 testes, 82% de cobertura nos módulos testáveis)
* **Lint/Formatação:** `ruff` + `black`
* **Configuração de Ambiente:** `python-dotenv`

### Início Rápido
```bash
# 1. Configure as credenciais
cp .env.example .env
# edite o .env com usuário/senha do MySQL

# 2. Inicialize o banco (rode uma vez)
mysql -u root -p < schema.sql

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Rode a aplicação
python src/main.py
```

### Estrutura do Projeto
```
FlowLog/
├── src/                  # Código da aplicação
│   ├── main.py           # Ponto de entrada + menu
│   ├── database.py       # Pool MySQL
│   ├── auth.py           # Decorator de RBAC
│   ├── session.py        # Sessão em memória
│   ├── exceptions.py     # Hierarquia de exceções do domínio
│   ├── repositories/     # Acesso a SQL (um por entidade)
│   ├── services/         # Lógica de negócio
│   └── *.py              # Módulos de feature (finos)
├── tests/                # Suíte de testes pytest (123 testes)
├── schema.sql            # Schema do banco
├── migrations/           # Upgrades de versão
├── scripts/              # Utilitários standalone
├── .env.example          # Template de configuração
├── CHANGELOG.md          # Notas de release
└── QA_REPORT.md          # Auditoria de qualidade (v1.4b)
```

Veja `CHANGELOG.md` para o histórico completo de versões.
