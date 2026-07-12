# Changelog

Todas as mudanças notáveis do projeto são documentadas aqui.
O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e o projeto segue [Versionamento Semântico](https://semver.org/lang/pt-BR/).

*All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).*

## [Unreleased]

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
