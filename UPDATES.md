# 📋 FlowLog Updates

> Release notes e changelog oficial do projeto. Acompanhe cada nova versão por aqui.
>
> *Official release notes and changelog. Track every new version here.*

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
