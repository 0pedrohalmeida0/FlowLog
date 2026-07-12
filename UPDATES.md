# 📋 FlowLog Updates

> Release notes e changelog oficial do projeto. Acompanhe cada nova versão por aqui.
>
> *Official release notes and changelog. Track every new version here.*

---

## v1.2 — 12 de julho de 2026 (em andamento)

> *"Fechando as brechas óbvias antes de crescer."*
> *"Closing the obvious gaps before scaling."*

> **Esta versão está sendo entregue em duas partes (v1.2a e v1.2b).**
> v1.2a já está no `main` (segurança). v1.2b vem logo em seguida (qualidade e CI).
> *This version is being shipped in two parts (v1.2a and v1.2b). v1.2a is already on `main` (security). v1.2b follows shortly (quality and CI).*

### v1.2a — Segurança 🔒

#### 🇧🇷 Versão em Português

**Destaques:** proteção contra brute-force, sessão com expiração automática, validação de complexidade de senha, fim do comportamento de "digita errado e o sistema fecha", arquivo `.env.example` versionado.

**Em uma frase:** o login agora bloqueia a conta após 5 tentativas falhas por 15 minutos, e a sessão encerra sozinha se o terminal ficar 30 minutos ocioso.

#### 🔐 Proteção contra brute-force

- **Bloqueio de conta após 5 tentativas falhas.** A partir da 6ª tentativa consecutiva com senha errada, a conta fica bloqueada por 15 minutos. O contador é zerado em login bem-sucedido. As credenciais (host, duração, quantidade) são configuráveis via `.env` — `LOCKOUT_MAX_ATTEMPTS` e `LOCKOUT_DURATION_MINUTES`.
- **Mensagem com tempo restante.** Quando o usuário tenta logar em conta bloqueada, o sistema mostra "~X min até o desbloqueio". O log registra o bloqueio com WARNING.
- **Resistente a user enumeration.** A mensagem de "usuário não encontrado" é a mesma de "senha incorreta" — um atacante não consegue descobrir quais usernames existem.

#### ⏰ Sessão com expiração automática

- **Auto-logout por inatividade.** Após 30 minutos sem interação, a sessão encerra e o sistema volta para a tela de login. Configurável via `SESSION_TIMEOUT_MINUTES` no `.env`. Para desabilitar, defina como `0`.
- **Re-prompt de login amigável.** Antes desta versão, digitar a senha errada encerrava o sistema. Agora, o login é re-prompted: o usuário pode tentar de novo, ou digitar `Q` no campo de usuário para sair.

#### 🛡️ Validação de complexidade de senha

- **Mínimo 6 caracteres, com pelo menos 1 letra e 1 número.** Senhas como `123` ou `abcdef` agora são rejeitadas no cadastro. A regra está em `utils.validar_senha_complexidade()` e é testável.
- **Feedback claro no cadastro.** O loop de cadastro mostra a regra específica violada e só prossegue quando o usuário fornece uma senha que passa.

#### ⚙️ Configuração externalizada

- **`.env.example` na raiz do projeto.** Lista todas as variáveis lidas pelo sistema, com valores default comentados. Copie para `.env` e preencha.
- **`requirements-dev.txt`** separa dependências de desenvolvimento (pytest, ruff, black, mypy) das de produção.

#### 📊 Antes e depois

| Aspecto                          | Antes                                          | Agora                                                                 |
|----------------------------------|------------------------------------------------|-----------------------------------------------------------------------|
| 5 tentativas erradas             | Ilimitadas, sistema fecha a cada erro          | Conta bloqueada por 15 min, log registra o bloqueio                   |
| Sessão ociosa                    | Nunca expirava (terminal aberto = qualquer um) | Auto-logout em 30 min (configurável)                                 |
| Senha fraca no cadastro          | Qualquer string não-vazia passava              | Mínimo 6 chars + letra + número                                      |
| Senha errada                     | Programa encerrava                              | Re-prompt, opção de sair com `Q`                                     |
| Variáveis de configuração        | Sem template, .env não versionado              | `.env.example` versionado, com todas as opções documentadas          |

#### 📋 Migração

```bash
mysql -u root -p flowlog < migrations/v1.1_to_v1.2.sql
```

Adiciona colunas `tentativas_falhas` e `bloqueado_ate` à tabela `usuarios`. Não exige recadastrar usuários — colunas novas têm default seguro (`0` e `NULL`).

#### 🇺🇸 English Version

**Highlights:** brute-force protection, automatic session expiration, password complexity validation, no more "type wrong and the system quits", versioned `.env.example`.

**In one sentence:** the login now locks the account after 5 failed attempts for 15 minutes, and the session ends by itself if the terminal sits idle for 30 minutes.

#### 🔐 Brute-force protection

- **Account lockout after 5 failed attempts.** From the 6th consecutive wrong password, the account is blocked for 15 minutes. Counter is reset on successful login. Settings (host, duration, count) are configurable via `.env` — `LOCKOUT_MAX_ATTEMPTS` and `LOCKOUT_DURATION_MINUTES`.
- **Message with remaining time.** When the user tries to log into a blocked account, the system shows "~X min until unlock". The log records the block with WARNING.
- **Resistant to user enumeration.** "User not found" and "wrong password" return the same message — an attacker cannot discover which usernames exist.

#### ⏰ Session auto-expiration

- **Auto-logout on inactivity.** After 30 minutes without interaction, the session ends and the system returns to the login screen. Configurable via `SESSION_TIMEOUT_MINUTES` in `.env`. Set to `0` to disable.
- **Friendly login re-prompt.** Before this version, a wrong password would close the system. Now, the login re-prompts: the user can try again, or type `Q` at the username field to quit.

#### 🛡️ Password complexity validation

- **Minimum 6 characters, with at least 1 letter and 1 number.** Passwords like `123` or `abcdef` are now rejected at registration. The rule is in `utils.validar_senha_complexidade()` and is testable.
- **Clear feedback at registration.** The registration loop shows the specific rule violated and only proceeds when the user provides a valid password.

#### ⚙️ Externalized configuration

- **`.env.example` at project root.** Lists all variables read by the system, with default values commented. Copy to `.env` and fill in.
- **`requirements-dev.txt`** separates dev dependencies (pytest, ruff, black, mypy) from production ones.

#### 📊 Before and after

| Aspect                          | Before                                          | Now                                                                   |
|---------------------------------|-------------------------------------------------|-----------------------------------------------------------------------|
| 5 wrong attempts                | Unlimited, system closes on each error          | Account locked for 15 min, log records the block                      |
| Idle session                    | Never expired (open terminal = anyone)          | Auto-logout at 30 min (configurable)                                  |
| Weak password at registration   | Any non-empty string worked                     | Min 6 chars + letter + number                                        |
| Wrong password                  | Program exited                                  | Re-prompt, option to quit with `Q`                                   |
| Configuration variables         | No template, .env not versioned                 | `.env.example` versioned, all options documented                     |

#### 📋 Migration

```bash
mysql -u root -p flowlog < migrations/v1.1_to_v1.2.sql
```

Adds `tentativas_falhas` and `bloqueado_ate` columns to the `usuarios` table. No user re-registration needed — new columns have safe defaults (`0` and `NULL`).

---

### v1.2b — Qualidade e CI 🧪

#### 🇧🇷 Versão em Português

**Destaques:** primeira suite de testes automatizados, CI rodando em todo push, configuração centralizada de ferramentas, `CHANGELOG.md` documentando a história do projeto.

**Em uma frase:** agora qualquer contribuição passa por `ruff` + `black` + `pytest` automaticamente no GitHub, então regressões são pegas antes de chegar em produção.

#### 🧪 Testes automatizados

- **Suite inicial com pytest.** Cobre os módulos puros (sem dependência de MySQL): CNPJ (10 casos), bcrypt (8 casos), validação de complexidade de senha (7 casos), sessão (10 casos incluindo expiração), decorator `@requer_nivel` (7 casos de RBAC). **42 testes** no total.
- **`tests/conftest.py`** com path injection (não precisa instalar o pacote) e fixture de isolamento de sessão (cada teste começa com sessão vazia).
- **`pyproject.toml`** centraliza config de pytest, black, ruff, mypy e coverage. Sumiu o `pytest.ini` solto, o `setup.cfg` e o `mypy.ini` — tudo num lugar.

#### ⚙️ Lint e format

- **Ruff** para lint (substitui flake8 + isort + pyupgrade + bugbear com performance muito maior).
- **Black** para formatação, com `line-length=100`.
- **Mypy** instalado mas com `disallow_untyped_defs = false` por enquanto — strict mode fica para a v1.4 (quando o código já tiver type hints).
- **Cobertura mínima de 50%** no CI (subindo para 70% na v1.3, 80% na v1.4).

#### 🤖 CI no GitHub Actions

- **Roda em Python 3.10, 3.11 e 3.12** (matriz completa).
- **Cache de pip** para builds mais rápidos.
- **3 estágios:** `ruff check` → `black --check` → `pytest --cov`.
- **Dispara em push para main e em todo PR.** PR que quebrar teste ou lint não pode ser mergeado.

#### 📝 Documentação adicional

- **`CHANGELOG.md` no padrão Keep a Changelog.** Histórico formal do projeto, em PT/EN, separado do `UPDATES.md` (que continua sendo o release notes focado em cliente).
- **`.github/workflows/ci.yml`** versionado e pronto pra customizar.

#### 📊 Antes e depois

| Aspecto                          | Antes                                          | Agora                                                                 |
|----------------------------------|------------------------------------------------|-----------------------------------------------------------------------|
| Cobertura de testes              | Zero — tudo era teste manual                    | 42 testes automatizados cobrindo utils, session, auth                 |
| Verificação de PRs               | Manual (reviewer tinha que rodar testes)        | Automática — CI roda lint + format + test em todo push               |
| Lint / format                    | Inconsistente entre arquivos                    | Ruff + Black rodando no CI, configuração em pyproject.toml           |
| Histórico do projeto             | Difícil de seguir (só git log)                  | `CHANGELOG.md` no padrão Keep a Changelog                            |
| Configuração de ferramentas      | Espalhada em vários arquivos                    | Centralizada em `pyproject.toml`                                     |

#### 🇺🇸 English Version

**Highlights:** first automated test suite, CI running on every push, centralized tool configuration, `CHANGELOG.md` documenting the project's history.

**In one sentence:** now every contribution goes through `ruff` + `black` + `pytest` automatically on GitHub, so regressions are caught before reaching production.

#### 🧪 Automated tests

- **Initial pytest suite.** Covers pure modules (no MySQL dependency): CNPJ (10 cases), bcrypt (8 cases), password complexity validation (7 cases), session (10 cases including expiration), `@requer_nivel` decorator (7 RBAC cases). **42 tests** total.
- **`tests/conftest.py`** with path injection (no need to install the package) and session isolation fixture (each test starts with empty session).
- **`pyproject.toml`** centralizes pytest, black, ruff, mypy and coverage config. Gone are the loose `pytest.ini`, `setup.cfg` and `mypy.ini` — everything in one place.

#### ⚙️ Lint and format

- **Ruff** for lint (replaces flake8 + isort + pyupgrade + bugbear with much better performance).
- **Black** for formatting, with `line-length=100`.
- **Mypy** installed but with `disallow_untyped_defs = false` for now — strict mode comes in v1.4 (when code already has type hints).
- **Minimum coverage 50%** in CI (rising to 70% in v1.3, 80% in v1.4).

#### 🤖 CI on GitHub Actions

- **Runs on Python 3.10, 3.11 and 3.12** (full matrix).
- **pip cache** for faster builds.
- **3 stages:** `ruff check` → `black --check` → `pytest --cov`.
- **Triggers on push to main and every PR.** PRs that break tests or lint cannot be merged.

#### 📝 Additional documentation

- **`CHANGELOG.md` in Keep a Changelog format.** Formal project history, in PT/EN, separate from `UPDATES.md` (which remains the customer-focused release notes).
- **`.github/workflows/ci.yml`** versioned and ready to customize.

#### 📊 Before and after

| Aspect                          | Before                                          | Now                                                                   |
|---------------------------------|-------------------------------------------------|-----------------------------------------------------------------------|
| Test coverage                   | Zero — everything was manual testing             | 42 automated tests covering utils, session, auth                       |
| PR verification                 | Manual (reviewer had to run tests)               | Automatic — CI runs lint + format + test on every push                |
| Lint / format                   | Inconsistent across files                       | Ruff + Black running in CI, configuration in pyproject.toml           |
| Project history                 | Hard to follow (git log only)                   | `CHANGELOG.md` in Keep a Changelog format                             |
| Tool configuration              | Scattered across multiple files                 | Centralized in `pyproject.toml`                                       |

---

## v1.1 — 12 de julho de 2026

> *"Auditoria de verdade, controle de acesso limpo, Curva ABC que ajuda a decidir."*
> *"Real audit trail, clean access control, a Curva ABC that actually helps you decide."*

---

### 🇧🇷 Versão em Português

#### ✨ Destaques desta versão

Esta release transforma o FlowLog de um sistema que *registra operações* em um sistema que *dá resposta sobre quem fez o quê*. Agora cada movimentação no histórico carrega o usuário que a registrou, o controle de acesso foi reescrito do zero, e o relatório de Curva ABC finalmente classifica seus produtos em A/B/C com o critério de Pareto 80/15/5.

**Em uma frase:** agora você sabe quem registrou cada saída, o sistema bloqueia o que cada perfil pode fazer de forma centralizada, e a Curva ABC te diz onde colocar seu esforço de gestão de estoque.

#### 👤 Auditoria: agora sabemos quem fez o quê

- **Identidade em toda movimentação.** Cada entrada e saída no histórico passa a registrar o `usuario_id` de quem a executou. A tabela `historico_movimentacoes` ganhou uma coluna com chave estrangeira para `usuarios`. Linhas antigas permanecem legíveis: o relatório usa `LEFT JOIN` e exibe `(sistema)` quando o usuário não está registrado.
- **Histórico mais útil.** O relatório de movimentações ganhou uma coluna `USUÁRIO` ao lado do produto, tipo e quantidade. Filtrar por usuário, exportar logs de auditoria, e investigar discrepâncias agora é trivial.

#### 🔐 Controle de acesso: limpo e centralizado

- **Decorator `@requer_nivel(N)`.** O `if nivel == 1: print("Acesso Negado")` que se repetia 7 vezes no menu principal foi extinto. Agora cada handler de opção declara seu requisito de nível uma vez, com o decorator, e a checagem é centralizada em `auth.py`.
- **Hierarquia clara.** Nível 1 (Operador) tem acesso apenas a consultas. Nível 2 (Gerente) opera o estoque. Nível 3 (Admin TI) gerencia usuários. Tentar acessar uma opção acima do seu nível agora registra um WARNING no log com nome do usuário e função tentada — pronto para auditoria de tentativas de acesso.
- **Sessão única do app.** Um módulo `session.py` mantém o estado do usuário logado (id, username, nível, timestamp de login) em memória. Outros módulos consultam esse estado sem precisar carregar variáveis globais espalhadas.

#### 📊 Curva ABC: de ordenação a classificação de verdade

- **Classificação A/B/C real.** O relatório agora aplica o critério de Pareto: produtos responsáveis pelos primeiros **80%** do volume de saída são **A** (alto giro, foco principal); os próximos **15%** (80–95%) são **B** (giro intermediário); os **5%** finais são **C** (baixo giro, candidatos a revisão). O cálculo é feito em SQL com window function (`SUM ... OVER ORDER BY ...`) — sem N+1 queries, sem código Python iterando.
- **Resumo executivo.** No final do relatório, um bloco diz "X produtos classe A, Y classe B, Z classe C". Use isso na reunião de planejamento.

#### 🛠️ Operação e infraestrutura

- **Pool de conexões MySQL.** A camada de banco agora usa `MySQLConnectionPool` (singleton por classe). Conexões são reusadas em vez de abertas/fechadas a cada operação. Em escala, isso evita o overhead de criar sockets TCP a cada chamada.
- **Logging estruturado com rotação.** Todos os `print()` de mensagens de status foram migrados para o módulo `logging`, com níveis (DEBUG/INFO/WARNING/ERROR), timestamps e saída simultânea em console + arquivo `logs/flowlog.log` com rotação automática (10 MB × 5 backups). Suporte, auditoria e debugging agora têm o que precisam.

#### 📊 Antes e depois

| Aspecto                          | Antes                                          | Agora                                                                 |
|----------------------------------|------------------------------------------------|-----------------------------------------------------------------------|
| Quem registrou a saída X?        | Impossível saber                               | Exibido no relatório e gravado no banco                               |
| Permissão por operação           | Repetida em 7 `if`s no `main.py`               | Declarada com `@requer_nivel(N)` em cada handler                      |
| Tentativa de acesso negado       | Só mensagem no console                         | Mensagem no console + WARNING no log com usuário e função             |
| Relatório de "Curva ABC"         | Lista ordenada por total de saídas             | Classificação A/B/C por Pareto 80/15/5 + resumo executivo            |
| Conexão ao banco                 | Nova a cada chamada                            | Reusada via pool singleton                                            |
| Logs de operação                 | `print()` no console (some quando fecha)       | Console + arquivo rotativo (10 MB × 5 backups)                        |
| Sessão do usuário                | Só o nível, retornado pelo login               | `session.py` com id, username, nível, timestamp                      |

#### 📋 O que muda para instalações existentes

> ⚠️ **Atenção:** esta versão altera o schema do banco. Você precisa rodar a migration antes de subir a nova versão do app.

Em resumo, para atualizar:

1. Faça backup do banco (`mysqldump`).
2. Rode a migration: `mysql -u root -p flowlog < migrations/v1.0_to_v1.1.sql`
3. Substitua os arquivos de `src/` (incluindo os três novos: `session.py`, `auth.py`, `logging_config.py`).
4. Substitua `schema.sql` pela nova versão (apenas para referência futura — não precisa rodar de novo).
5. Rode o app: o diretório `logs/` será criado automaticamente na primeira execução.

A coluna `usuario_id` é criada como NULL permitida: linhas legadas permanecem válidas, e o relatório exibe `(sistema)` para elas. Nenhum dado é perdido.

#### 🚀 Próximas entregas (preview)

- 🔐 **Bloqueio de conta** após N tentativas falhas de login (com contador e cooldown).
- ✏️ **Edição de produtos** (hoje só é possível excluir e recadastrar).
- 📦 **Instalador gráfico** com PyInstaller + Inno Setup.
- 📈 **Dashboard de auditoria** com tentativas de acesso negado, operações por usuário, etc.

---

### 🇺🇸 English Version

#### ✨ Highlights of this release

This release turns FlowLog from a system that *logs operations* into one that *answers who did what*. Every movement in the history now carries the user who performed it, access control has been rewritten from scratch, and the Curva ABC report finally classifies your products in A/B/C with the 80/15/5 Pareto criterion.

**In one sentence:** you now know who registered each outbound, the system blocks what each profile can do in a centralized way, and the Curva ABC tells you where to focus your inventory management effort.

#### 👤 Audit trail: we know who did what

- **Identity on every movement.** Each entry and exit in the history now records the `usuario_id` of the user who executed it. The `historico_movimentacoes` table has a new foreign key column to `usuarios`. Legacy rows remain readable: the report uses `LEFT JOIN` and shows `(sistema)` when the user is not registered.
- **A more useful history.** The movements report gained a `USUÁRIO` column next to product, type and quantity. Filtering by user, exporting audit logs and investigating discrepancies are now trivial.

#### 🔐 Access control: clean and centralized

- **`@requer_nivel(N)` decorator.** The `if nivel == 1: print("Acesso Negado")` that was repeated 7 times in the main menu is gone. Each option handler now declares its level requirement once, with the decorator, and the check is centralized in `auth.py`.
- **Clear hierarchy.** Level 1 (Operator) has read-only access. Level 2 (Manager) operates the stock. Level 3 (IT Admin) manages users. Attempting an option above your level now records a WARNING in the log with the username and function attempted — ready for access-attempt auditing.
- **Single app session.** A `session.py` module holds the logged-in user's state (id, username, level, login timestamp) in memory. Other modules query that state without scattered global variables.

#### 📊 Curva ABC: from ordering to real classification

- **Real A/B/C classification.** The report now applies the Pareto criterion: products responsible for the first **80%** of outbound volume are **A** (high turnover, main focus); the next **15%** (80–95%) are **B** (intermediate turnover); the final **5%** are **C** (low turnover, candidates for review). The calculation runs in SQL with a window function (`SUM ... OVER ORDER BY ...`) — no N+1 queries, no Python iteration.
- **Executive summary.** At the end of the report, a block says "X products class A, Y class B, Z class C". Use it in the planning meeting.

#### 🛠️ Operations and infrastructure

- **MySQL connection pool.** The database layer now uses `MySQLConnectionPool` (class-level singleton). Connections are reused instead of opened/closed per operation. At scale, this avoids the overhead of creating TCP sockets for every call.
- **Structured logging with rotation.** All status-message `print()` calls have been migrated to the `logging` module, with levels (DEBUG/INFO/WARNING/ERROR), timestamps, and simultaneous output to console + `logs/flowlog.log` with automatic rotation (10 MB × 5 backups). Support, audit, and debugging now have what they need.

#### 📊 Before and after

| Aspect                          | Before                                          | Now                                                                   |
|---------------------------------|-------------------------------------------------|-----------------------------------------------------------------------|
| Who registered exit X?          | Impossible to know                              | Shown in the report and stored in the database                        |
| Permission per operation        | Repeated in 7 `if`s in `main.py`                | Declared with `@requer_nivel(N)` on each handler                      |
| Denied access attempt           | Console message only                            | Console message + WARNING in log with user and function               |
| "Curva ABC" report              | Sorted list by total exits                      | A/B/C classification by 80/15/5 Pareto + executive summary            |
| Database connection             | New per call                                    | Reused via singleton pool                                             |
| Operation logs                  | `print()` to console (lost when closed)         | Console + rotating file (10 MB × 5 backups)                           |
| User session                    | Just the level, returned by login               | `session.py` with id, username, level, timestamp                      |

#### 📋 What changes for existing installations

> ⚠️ **Attention:** this version alters the database schema. You need to run the migration before deploying the new app version.

In short, to upgrade:

1. Back up the database (`mysqldump`).
2. Run the migration: `mysql -u root -p flowlog < migrations/v1.0_to_v1.1.sql`
3. Replace the `src/` files (including three new ones: `session.py`, `auth.py`, `logging_config.py`).
4. Replace `schema.sql` with the new version (for future reference only — no need to re-run).
5. Run the app: the `logs/` directory will be created automatically on first execution.

The `usuario_id` column is created as nullable: legacy rows remain valid, and the report shows `(sistema)` for them. No data is lost.

#### 🚀 Coming next (preview)

- 🔐 **Account lockout** after N failed login attempts (with counter and cooldown).
- ✏️ **Product editing** (today you can only delete and re-register).
- 📦 **Graphical installer** with PyInstaller + Inno Setup.
- 📈 **Audit dashboard** with denied access attempts, operations per user, etc.

---

## v1.0 — 12 de julho de 2026

> *"De protótipo para produto — segurança, integridade e profissionalismo de ponta a ponta."*
> *"From prototype to product — end-to-end security, integrity, and professionalism."*

### 🇧🇷 Versão em Português

#### ✨ Destaques desta versão

Esta release marca um salto de qualidade do FlowLog. O sistema sai de um estágio de protótipo funcional e entra em um patamar de **produto com fundamentos sólidos de segurança e integridade de dados**.

**Em uma frase:** as senhas dos usuários agora são protegidas com criptografia industrial, e cada movimentação de estoque acontece como uma operação única e atômica — se algo falhar, nada fica pela metade.

#### 🔒 Segurança reforçada

- **Criptografia de senhas com bcrypt.** Senhas armazenadas com bcrypt. Mesma proteção usada por bancos e sistemas profissionais.
- **Senha invisível durante o login.** Senha digitada de forma oculta via `getpass`.
- **Validação rigorosa de CNPJ.** Verificação de dígitos verificadores antes de aceitar um CNPJ.

#### ⚡ Integridade de dados

- **Transações atômicas em entradas e saídas.** UPDATE em `produtos` e INSERT em `historico_movimentacoes` na mesma transação.
- **Proteção contra concorrência.** `SELECT ... FOR UPDATE` trava a linha do produto durante a operação.
- **Filtro de histórico blindado.** Query parametrizada via dicionário de constantes — sem concatenação de input do usuário.

#### 🛠️ Operação e instalação

- **Schema SQL documentado.** `schema.sql` formal com índices, FKs e constraints.
- **Guia de migração passo a passo.** `MIGRATION.md` para atualizar instalações existentes.

#### 📋 O que muda para instalações existentes

> ⚠️ **Atenção:** se você já tem o FlowLog em uso, esta versão exige migração manual. Todos os usuários precisam ser recadastrados porque o sistema não consegue converter senhas antigas (em texto puro) para bcrypt — e isso é proposital, é assim que criptografia boa funciona.

Para atualizar: backup → `ALTER TABLE` em `usuarios.senha` (ou recriar do zero) → atualizar `pip install` → substituir arquivos `src/` → recadastrar usuários.

---

### 🇺🇸 English Version

#### ✨ Highlights of this release

This release marks a quality leap for FlowLog. The system leaves the "functional prototype" stage and steps into the level of a **product with solid security and data integrity foundations**.

**In one sentence:** user passwords are now protected with industrial-grade encryption, and every stock movement happens as a single, atomic operation — if anything fails, nothing is left half-done.

#### 🔒 Strengthened security

- **Password encryption with bcrypt.** Same standard used by banks and security-conscious applications.
- **Hidden password at the terminal.** Typed invisibly via `getpass`.
- **Strict CNPJ validation.** Check digits verified before accepting a CNPJ.

#### ⚡ Data integrity

- **Atomic transactions on inbound and outbound.** UPDATE on `produtos` and INSERT on `historico_movimentacoes` in the same transaction.
- **Concurrency protection.** `SELECT ... FOR UPDATE` locks the product row during the operation.
- **Hardened history filter.** Parameterized query via constants dictionary — no user input concatenation.

#### 🛠️ Operations and installation

- **Documented SQL schema.** Formal `schema.sql` with indexes, FKs and constraints.
- **Step-by-step migration guide.** `MIGRATION.md` for upgrading existing installations.

#### 📋 What changes for existing installations

> ⚠️ **Attention:** if you already have FlowLog in use, this version requires a manual migration. All users need to be re-registered because the system cannot convert old (plaintext) passwords to bcrypt — and that's by design. That's how good encryption works.

To upgrade: backup → `ALTER TABLE` on `usuarios.senha` (or recreate from scratch) → update `pip install` → replace `src/` files → re-register users.

---

<p align="center">
  <sub>
    Dúvidas ou problemas com a migração? Abra uma <em>issue</em> no repositório.<br>
    Questions or issues with the migration? Open an <em>issue</em> in the repository.
  </sub>
</p>
