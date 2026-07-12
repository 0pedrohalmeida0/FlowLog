# Changelog

Todas as mudanças notáveis do projeto são documentadas aqui.
O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e o projeto segue [Versionamento Semântico](https://semver.org/lang/pt-BR/).

*All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).*

## [Unreleased]

### Estratégia (v1.5+ — virada de negócio)
- **2 SKUs definidos** (refinamento — era 3, agora consolida):
  - **FlowLog Licença** — software on-premise, instalável Windows/Linux, com **todas as features premium embutidas** (multi-filial, API REST local, LDAP, audit, dashboard, white-label). One-time ou anual.
  - **FlowLog Cloud** — SaaS web, multi-tenant, billing recorrente (Free / Pro / Business). Mensal.
- **Roadmap reescrito** — 5 versões (v1.5 → v3.0) cobrindo Licença → Licença + Premium → Cloud MVP → Cloud GA → IA.
- **Stack Cloud definida** — FastAPI + SQLAlchemy + PostgreSQL + React + Stripe/ASAAS + Docker.
- **Estimativa até Cloud GA**: 5-7 meses, foco em receita recorrente.

Ver `ROADMAP.md` para o plano completo.

## [1.4.2] - 2026-07-12

### Security (v1.4d — segundo QA pass: bugs latentes)
- **CR-07** CNPJ com dígitos Unicode (árabe ٠-٩, etc.) **rejeitado**.
  Antes: `normalize_cnpj("٣٣٠٠٠١٦٧٠٠٠١٠١")` retornava uma string
  de dígitos arábicos diferente da versão ASCII, levando a
  **duplicação silenciosa de fornecedor** (o UNIQUE constraint
  do banco não detectava). Agora: `validar_cnpj` retorna False
  e `normalize_cnpj` levanta `ValueError` quando o input tem
  apenas caracteres não-ASCII.
- **CR-08** **CSV export** agora sanitiza contra CVE-2014-3524
  (paridade com AL-03 do import). Produtos cadastrados direto
  pela interface (não via CSV) com nome começando em `=`, `+`,
  `-`, `@`, TAB ou CR são prefixados com `'` no export.

### Fixed (v1.4d)
- **ME-11** `validar_senha_complexidade` aceita `bytes` e `int`
  sem explodir com `TypeError`. Decodifica bytes em UTF-8 e
  rejeita outros tipos.
- **ME-12** `editar_produto` agora usa a mesma função
  `_parse_preco` do csv_import, aceitando "10,50", "10.50" e
  "1.234,56" (formato BR completo). Antes: "1.234,56" virava
  "1.234" (perdia precisão).
- **ME-13** `cadastrar_usuario` agora aplica `.strip()` na
  senha antes de criar. Antes: "  abc123  " criava senha com
  whitespace.
- **ME-14** `listar_produtos` agora trata defensivamente caso
  `service.listar_todos()` retorne `None` (em testes/mocks).
- **ME-15** `verificar_senha` agora chama `bcrypt.checkpw` com
  hash dummy quando o hash é texto puro (mitigação teórica
  de timing attack que poderia vazar o tipo de hash).
- **BA-09** `normalize_cnpj(None)` agora levanta `ValueError`
  em vez de retornar string vazia silenciosamente.

### Added (v1.4d)
- 18 testes novos (total 138, cobertura 82%):
  - `tests/test_utils.py` — 4 testes (CR-07 CNPJ Unicode, ME-11
    bytes, BA-09 None, validação).
  - `tests/test_csv.py` — novo arquivo, 9 testes (CR-08
    sanitização no export).
- `_csv_safe` em `csv_export.py` (paridade com import).
- `_parse_preco` em `editar_produto.py` (paridade com import).

## [1.4.1] - 2026-07-12

### Security (v1.4c — QA patch: correções críticas)
- **CR-01** Senha do MySQL **não vai mais na linha de comando** (`backup.py`).
  Antes: `mysqldump -uroot -pSenha123 ...` (visível em `ps aux`).
  Agora: senha via env var `MYSQL_PWD` + `env=` no `subprocess.run`.
  Defesa em profundidade: `env.pop('MYSQL_PWD')` após o call.
- **CR-03** **bcrypt 72-byte limit** contornado. Senhas arbitrariamente
  longas agora funcionam (acentos, emoji, etc.) via pré-normalização
  com SHA-256 antes do bcrypt. `hash_senha` e `verificar_senha`
  aplicam a mesma transformação.
- **CR-06** Logs do driver MySQL **sanitizados** (`database.py`).
  `Database._sanitize_error` remove `password=`, `user=`, `host=`,
  `port=` da mensagem antes de logar.
- **AL-03** **CSV Injection (CVE-2014-3524)** mitigada no import
  (`csv_import._csv_safe`). Nomes de produto que começam com `=`, `+`,
  `-`, `@`, `\t`, `\r` são prefixados com `'` antes de gravar.

### Fixed (v1.4c)
- **CR-02** `relatorio_curva.py` agora fecha o cursor **depois** do
  export. Antes o export da Curva ABC falhava com "Cursor closed".
- **CR-04** Edição de produto usa `SELECT ... FOR UPDATE` dentro da
  transação. Fim do lost-update entre gerentes editando o mesmo
  produto ao mesmo tempo. Adicionado `ProdutoRepository.buscar_por_id_locked`.
- **CR-05** Import CSV agora **pré-resolve fornecedores por CNPJ único**
  antes de inserir produtos. CNPJs duplicados no mesmo CSV usam o
  mesmo fornecedor (sem UNIQUE error + rollback total).
- **AL-01/AL-02** `ver_historico` agora pergunta o limite ao usuário
  (padrão 200) e inclui o **ano** no formato de data (`%d/%m/%Y %H:%M`).
  Adiciona aviso "exibindo X de Y" quando há mais.
- **ME-04** Curva ABC usa margem de 0.0001 para evitar misclass por
  float (0.80 pode ser 0.79999... por precisão IEEE-754).
- **ME-05** `editar_produto` agora exibe a `data_entrada` do produto
  no resumo (que estava no SELECT mas era ignorada).
- **ME-06** `listar_produtos` agora pergunta o limite ao usuário
  (padrão 50) e avisa quando há mais produtos.
- **ME-07** `LOG_LEVEL` agora é lido do .env pelo `setup_logging`
  (antes era hardcoded em INFO).
- **ME-10** `main._loop_menu` agora captura `FlowLogError` (mensagem
  amigável) e qualquer `Exception` (logada + mensagem genérica).
  Fim do crash do app por exception não-tratada.
- **ME-03** `BACKUP_MAX_RETENTION` agora é lido do .env (antes
  `MAX_BACKUPS_RELOCALES = 30` hardcoded em `backup.py`).

### Changed (v1.4c)
- **AL-04** `cadastrar_usuario.py` agora delega pra `UsuarioService`.
  Adicionado `src/services/usuario_service.py`.
- **AL-04** `listar_produtos.py` agora usa `ProdutoService` em vez de
  SQL inline. Continuam com feature module fino.
- **ME-01** Adicionados métodos públicos no `ProdutoService`:
  `buscar(id)`, `listar_todos()`, `listar_abaixo_do_minimo()`.
  Substituem o acesso direto a `service._produtos` pelos feature modules.
- **BA-02** `csv_export.py` agora importa `_SQL_CURVA_ABC` no topo
  (em vez de dentro da função). Elimina `noqa: PLC0415`.
- **BA-06** `src/services/__init__.py` reexporta todas as 6 services
  (Auth, Estoque, Produto, Fornecedor, Historico, Usuario).
- **BA-08** `src/teste_insercao.py` movido para `scripts/cadastro_teste.py`
  (era um script manual, não teste).
- **ME-08** `README.md` reescrito: features atuais, versão, badges
  de testes/cobertura, quick start, estrutura do projeto.
- `produto_repository.listar_todos` agora tem `ORDER BY id ASC`
  (antes sem ORDER BY, ordem não-determinística).

### Added (v1.4c)
- 13 testes novos (total 123, cobertura 82.3%):
  - `tests/test_utils.py` — 3 testes CR-03 (senhas longas,
    com acentos, realistas).
  - `tests/test_services.py` — 3 testes (CR-04 SELECT FOR UPDATE,
    rowcount=0, ME-01 fachada pública).
  - `tests/test_repositories.py` — 1 teste CR-04 (buscar_por_id_locked).
  - `tests/test_database.py` — novo arquivo, 6 testes de sanitização
    de erros.
- `QA_REPORT.md` — auditoria completa da v1.4b com 29 achados
  (6 críticos, 5 altos, 10 médios, 8 baixos).
- `scripts/cadastro_teste.py` — script de teste manual (movido de src/).

## [1.4.0] - 2026-07-12

### Added (v1.4b — Services + refactor dos feature modules)
- **`src/services/`** — camada de business logic que orquestra repositories:
  - `AuthService` — autenticação + lockout, lê `LOCKOUT_MAX_ATTEMPTS`/`LOCKOUT_DURATION_MINUTES` do .env.
  - `EstoqueService` — `registrar_entrada`/`registrar_saida` com transação atômica, `SELECT ... FOR UPDATE` e `usuario_id` da sessão.
  - `ProdutoService` — `cadastrar` (resolve fornecedor) e `editar` (whitelist de campos + snapshot JSON).
  - `FornecedorService` — `cadastrar`/`editar_razao_social`/`excluir` com validação de CNPJ.
  - `HistoricoService` — listagem com filtro de tipo.
- **Feature modules refatorados** (viram finos, só I/O de terminal):
  - `login.py` delega 100% pra `AuthService`, captura `ContaBloqueadaError`/`AuthenticationError`/`ValidationError` e traduz em mensagem amigável.
  - `entrada.py` e `saida_estoque.py` delegam pra `EstoqueService`, capturam `NotFoundError`/`EstoqueInsuficienteError`/`ValidationError`.
  - `cadastro_interativo.py` delega pra `ProdutoService.cadastrar`, captura `CNPJInvalidoError`/`ValidationError`.
  - `editar_produto.py` delega pra `ProdutoService.editar`, captura `NotFoundError`/`ValidationError`.
- **Padrão de exceções em uso**: feature modules nunca mais levantam `print()` de erro; levantam exceções do `src/exceptions.py` e o caller (CLI) traduz pra mensagem.
- **`tests/test_services.py`** (32 testes) — Auth/Estoque/Produto/Fornecedor com mocks de repository. Verifica exceções em casos de borda (CNPJ inválido, estoque insuficiente, campo vazio, ID inexistente, tentativa de editar quantidade).

### Notes (PT)
- Feature modules restantes (ver_historico, relatorio_curva, csv_export, csv_import, backup, listar_produtos, configurar_alerta, editar_fornecedor, excluir_fornecedor, gerenciar_fornecedor) **ainda usam SQL direto**. Migração completa fica pra v1.4c ou depois — a base está pronta e a migração é mecânica (substituir SQL inline por chamada de repository).
- UI/UX **não muda** — o usuário continua interagindo da mesma forma; o que mudou é a arquitetura interna.
- Cada service aceita o(s) repository(s) no construtor — em produção usa os globais, em testes recebe mocks. Isso é o que torna os services testáveis sem MySQL real.

### Notes (EN)
- Remaining feature modules (ver_historico, relatorio_curva, csv_export, csv_import, backup, listar_produtos, configurar_alerta, editar_fornecedor, excluir_fornecedor, gerenciar_fornecedor) **still use direct SQL**. Full migration goes in v1.4c or later — the foundation is in place and the migration is mechanical (replace inline SQL with repository calls).
- UI/UX **does not change** — users keep interacting the same way; what changed is the internal architecture.
- Each service accepts the repository(ies) in the constructor — production uses the globals, tests get mocks. That's what makes services testable without real MySQL.

### Added (v1.4a — Repository pattern + exception hierarchy)
- **`src/exceptions.py`** — hierarquia de exceções do domínio: `FlowLogError` (base) + `ValidationError`, `NotFoundError`, `BusinessRuleError`, `AuthenticationError`, `AuthorizationError`, `DatabaseError`, `InfrastructureError` + especializadas (`EstoqueInsuficienteError`, `ContaBloqueadaError`, `CNPJInvalidoError`). Feature modules vão passar a levantar estas exceções em vez de imprimir mensagens de erro.
- **`src/repositories/`** — camada de acesso a dados por entidade:
  - `BaseRepository` com `transaction()` context manager e `_connect()`.
  - `ProdutoRepository` — listar/buscar/criar/atualizar/listar_abaixo_do_minimo.
  - `FornecedorRepository` — buscar_por_cnpj/criar/excluir.
  - `UsuarioRepository` — split entre `buscar_para_auth` (com hash) e `buscar_por_username` (sem hash, para listagens).
  - `HistoricoRepository` — listar (com filtro de tipo) + `inserir()` que recebe cursor do chamador.
  - `LogEdicoesRepository` — registrar snapshot + listar por produto.
  - Convenção: SQL vive só aqui. Feature modules viram finos (orquestração, não SQL).
- **`tests/test_exceptions.py`** (10 testes) — hierarquia das exceções + propagação de mensagens.
- **`tests/test_repositories.py`** (16 testes) — SQL gerado pelos repositories via mock, sem precisar de MySQL real. Pega bugs como "UPDATE sem WHERE" ou "campo renomeado e ninguém percebeu".
- **`.coveragerc`** — arquivo separado (e não inline no pyproject.toml) pra ser robusto quando pytest roda de fora do diretório do projeto. `fail_under=70` no CI.
- **CI** (`ci.yml`) — atualizado pra usar `--cov-config=.coveragerc` e `fail_under=70`.

### Notes (PT)
Esta release é a **fundação** da v1.4: o SQL foi todo pra um lugar só e os feature modules ainda não foram migrados pra usar os repositories. Próximos commits (v1.4b) vão refatorar `login.py`, `entrada.py`, `saida_estoque.py` e amigos pra chamar repositories + services em vez de montar SQL diretamente. A UI/UX **não muda** — o usuário continua interagindo da mesma forma.

### Notes (EN)
This release is the **foundation** of v1.4: all SQL is now in one place, but feature modules haven't been migrated yet to use the repositories. Next commits (v1.4b) will refactor `login.py`, `entrada.py`, `saida_estoque.py` etc. to call repositories + services instead of assembling SQL directly. The UI/UX **does not change** — users keep interacting the same way.

## [1.3.0] - 2026-07-12

### Added (v1.3c — Backup + Sugestão de compra)
- **`src/backup.py`** — backup, listagem e restauração do banco via `mysqldump` / `mysql` no PATH. Sub-menu no app (opção 12). Backups salvos em `./backups/` com nome timestamped, retenção automática dos últimos 30.
- **Sugestão automática de compra** integrada ao alerta de estoque crítico. Para cada produto abaixo do mínimo, calcula `qtd_sugerida = max(alerta_minimo * 2 - quantidade_atual, 0)` (fórmula simples: repor até 2x o mínimo) e mostra nome do fornecedor. Aparece automaticamente no alerta do menu e na inicialização.
- **Opção 12 no menu** — "Backup e Restauração" (nível 2). Sub-menu: [1] Fazer backup / [2] Listar / [3] Restaurar (com confirmação dupla via digitação de `RESTAURAR`).
- `mysqldump` é chamado com `--single-transaction` (consistência sem lock), `--routines` e `--triggers` (preparação para v1.4+).

### Notes (PT)
- Backup manual via menu é o primeiro passo. Backup automático diário (cron-like) entra na v1.4 com a refatoração para `config.yaml`.
- Restauração tem confirmação dupla (digitar `RESTAURAR`) por ser destrutiva — apaga todos os dados atuais antes de popular com o dump.

### Notes (EN)
- Manual backup via menu is the first step. Automatic daily backup (cron-like) lands in v1.4 along with the `config.yaml` refactor.
- Restore has double confirmation (typing `RESTAURAR`) because it's destructive — it wipes all current data before populating from the dump.

### Added (v1.3b — CSV Import / Export)
- **`src/csv_export.py`** — exporta inventário, histórico (filtrado por tipo) e Curva ABC para CSV. Padrão BR: encoding `utf-8-sig` (BOM, abre direto no Excel), separador `;`, decimais com vírgula, quebras de linha `\r\n`. Cada relatório pergunta ao final se o usuário quer exportar.
- **`src/csv_import.py`** — importa produtos em massa a partir de CSV. Formato esperado: `nome,quantidade,preco_custo,fornecedor_cnpj,alerta_minimo` (cabeçalho obrigatório, `alerta_minimo` opcional). Aceita separador `;` ou `,` (auto-detecta) e decimais com `.` ou `,` (auto-converte). Valida CNPJ por linha; pula inválidas com aviso; confirma antes de inserir. Fornecedores inexistentes são cadastrados automaticamente.
- **Opção 11 no menu** — "Importar Produtos de CSV" (nível 2).
- **Listar Produtos, Ver Histórico, Curva ABC** agora oferecem export ao final de cada relatório.

### Notes (PT)
- v1.3b fecha o segundo bloco de feature mais pedido em qualquer demo: "posso abrir no Excel?" e "posso cadastrar em massa?". Export é BR-friendly de propósito (encoding BOM, separador `;`) — abre direto no Excel brasileiro sem precisar configurar nada.
- Import é defensivo: linhas inválidas são reportadas e puladas, nada é inserido sem confirmação explícita do usuário. Fornecedor novo vira `(importado CSV) CNPJ` na razão social — fácil de identificar e renomear depois.

### Notes (EN)
- v1.3b closes the second most-requested feature in any demo: "can I open it in Excel?" and "can I bulk-register?". Export is BR-friendly on purpose (BOM encoding, `;` separator) — opens directly in Brazilian Excel without configuration.
- Import is defensive: invalid lines are reported and skipped, nothing is inserted without explicit user confirmation. New suppliers become `(imported CSV) CNPJ` as the legal name — easy to identify and rename later.

### Added (v1.3a — Edição de produtos)
- **Edição de produto** no menu principal (opção 10). Permite editar nome, preço de custo e alerta mínimo.
- **Snapshot de auditoria** em nova tabela `produtos_historico_edicoes`. Cada edição grava o produto antes e depois em JSON, com referência ao usuário que editou.
- **Decisão de design:** edição de quantidade não é permitida no menu. Alterações de quantidade devem passar pelo fluxo de entrada/saída (opções 3 e 6) para preservar o histórico de movimentações. Quem precisa de ajuste manual usa SQL ou recurso de inventário físico (planejado para v1.3+).
- Nova migration: `migrations/v1.2_to_v1.3.sql` cria a tabela `produtos_historico_edicoes` com índices por `produto_id`, `data_edicao` e `usuario_id`.

### Migration
```bash
mysql -u root -p flowlog < migrations/v1.2_to_v1.3.sql
```
Cria a tabela `produtos_historico_edicoes` com 3 índices. Sem perda de dados.

### Notes (PT)
A v1.3 está sendo entregue em três partes. v1.3a (esta) fecha o maior buraco do CRUD: editar produtos. v1.3b trará exportação/importação CSV. v1.3c trará backup automático e sugestão de compra. UPDATES.md foi descontinuado em favor deste CHANGELOG (mais próximo do padrão da indústria).

### Notes (EN)
v1.3 is being shipped in three parts. v1.3a (this) closes the biggest CRUD gap: editing products. v1.3b will bring CSV import/export. v1.3c will bring automatic backup and purchase suggestions. UPDATES.md has been deprecated in favor of this CHANGELOG (closer to industry standard).

## [1.2.0] - 2026-07-12

### Added (v1.2a — Segurança)
- Account lockout after `LOCKOUT_MAX_ATTEMPTS` (default 5) failed logins, blocking for `LOCKOUT_DURATION_MINUTES` (default 15).
- User-enumeration resistance: identical error message for "user not found" and "wrong password".
- Auto-logout on inactivity via `SESSION_TIMEOUT_MINUTES` (default 30; set 0 to disable).
- Friendly login re-prompt: failed login no longer quits the program; user can press `Q` to exit.
- Password complexity validation: minimum 6 characters, at least 1 letter, at least 1 number.
- `.env.example` at project root with all configurable options documented.
- `requirements-dev.txt` separating dev dependencies (pytest, ruff, black, mypy) from production.
- New `utils.validar_senha_complexidade()` for testable password rules.
- New `session.registrar_atividade()` and `session.sessao_expirada()` helpers.

### Added (v1.2b — Qualidade)
- `pyproject.toml` with centralized tool config (pytest, black, ruff, mypy, coverage).
- Test suite with `pytest` covering CNPJ validation, bcrypt, password rules, session lifecycle and RBAC decorator.
- GitHub Actions CI: runs lint (`ruff`), format check (`black`), and tests with coverage on every push and PR.
- `CHANGELOG.md` (this file).
- `tests/conftest.py` with path injection and per-test session isolation.

### Changed
- `login.py` now uses dictionary cursor; logs every failure with WARNING.
- `main.py` outer loop re-prompts on failed login; inner loop checks session timeout.
- `cadastrar_usuario.py` loops until password passes complexity validation.

### Removed
- `LICENSE` file removed (per user request — proprietary intent until further notice).

### Migration
- New columns on `usuarios`: `tentativas_falhas INT NOT NULL DEFAULT 0`, `bloqueado_ate DATETIME NULL`.
- Apply with: `mysql -u root -p flowlog < migrations/v1.1_to_v1.2.sql`
- No data loss; new columns have safe defaults.

## [1.1.0] - 2026-07-12

### Added
- `usuario_id` foreign key in `historico_movimentacoes` (audit trail).
- `ver_historico` shows `USUÁRIO` column via `LEFT JOIN usuarios`.
- `@requer_nivel(N)` decorator in `auth.py`, replacing 7 repeated `if nivel == 1:` blocks in `main.py`.
- `session.py` with in-memory user state.
- Real Curva ABC (Pareto 80/15/5) using SQL window function `SUM ... OVER`.
- `logging_config.py` with `RotatingFileHandler` (10MB × 5 backups) and console output.
- `MySQLConnectionPool` singleton in `database.py` for connection reuse.
- All `print()` calls in feature modules replaced with `logger.info/warning/error`.

### Migration
- Apply: `mysql -u root -p flowlog < migrations/v1.0_to_v1.1.sql`

## [1.0.0] - 2026-07-12

### Added
- bcrypt password hashing (rejects legacy plaintext).
- Atomic transactions in `entrada.py` and `saida_estoque.py` with `SELECT ... FOR UPDATE`.
- Loop bug fix in `cadastro_interativo.py`.
- SQL Injection hardening in `ver_historico.py` (parameterized query, no f-string concatenation).
- CNPJ check-digit validation in `utils.validar_cnpj()`.
- `schema.sql` with full DDL (indexes, FKs, constraints).
- `MIGRATION.md` for v0.x → v1.0 upgrade.
- `getpass` for password input (hidden at terminal).

### Security
- Passwords stored as bcrypt hash (`VARCHAR(255)` column required).
- All existing plaintext passwords invalidated — users must re-register.
