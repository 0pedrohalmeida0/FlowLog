# Guia de Migração do FlowLog

> Como atualizar uma instalação existente para a versão mais recente.
> *How to upgrade an existing installation to the latest version.*

---

## v1.0 → v1.1 — Auditoria, RBAC, ABC de verdade, logging e pool

Esta versão traz uma rodada grande de melhorias. As principais mudanças que
exigem migração no banco de dados são:

### O que muda no banco

- **Nova coluna** `usuario_id` em `historico_movimentacoes` (FK para `usuarios.id`, NULL permitido).
  - Linhas legadas permanecem com `usuario_id = NULL` — a query de relatório usa
    `LEFT JOIN` e exibe `(sistema)` para o username nesse caso.

### Como aplicar a migration (banco existente)

```bash
mysql -u root -p flowlog < migrations/v1.0_to_v1.1.sql
```

Verificação rápida:

```sql
DESCRIBE historico_movimentacoes;
-- Deve mostrar a coluna usuario_id (INT NULL) e o índice idx_historico_usuario
```

### Como aplicar se for uma instalação fresh

Simplesmente rode o `schema.sql` do começo ao fim. Ele já está na versão v1.1.

```bash
mysql -u root -p < schema.sql
```

### Mudanças na aplicação

| Onde | Mudança | Impacto |
|------|---------|---------|
| `database.py` | Agora usa `MySQLConnectionPool` (singleton por classe) | Conexões são reusadas; sem mudança de comportamento observável |
| `main.py` | Substituído o `if nivel == 1: ...` por `@requer_nivel(N)` | Mesmo controle, sem repetição |
| `utils.registrar_log` | Nova assinatura: `(cursor, produto_id, tipo, quantidade, usuario_id)` | Chamada existente em `entrada.py` / `saida_estoque.py` foi atualizada |
| `ver_historico.py` | Relatório agora mostra a coluna `USUÁRIO` | Vem do `LEFT JOIN` em `usuarios` |
| `relatorio_curva.py` | Implementação real de Curva ABC (Pareto 80/15/5) | Saída do relatório agora inclui classe A/B/C e percentual |
| Logging | Todos os `print()` substituídos por `logger.info/warning/error` | Console continua mostrando mensagens; arquivo `logs/flowlog.log` agora é gerado com rotação |
| Novos módulos | `session.py`, `auth.py`, `logging_config.py` | Adicionados; nenhum efeito colateral sem usar |

### Como verificar que está tudo OK

```bash
python -m py_compile src/*.py
```

Deve compilar sem erros. Opcionalmente, abra o sistema e faça uma saída —
o `logs/flowlog.log` deve registrar a operação com seu `username`.

---

## v1.0 (recap) — bcrypt + transações atômicas

Esta versão anterior trouxe três mudanças de infra que exigiam ação
manual antes do primeiro start. Se você já está na v1.1, ignore esta
seção — só importa para instalações que ainda estão na v0.x e vão
pular direto para v1.1.

### 1. Senha agora é hash bcrypt

A coluna `senha` na tabela `usuarios` precisa estar dimensionada para
acomodar o hash bcrypt (60 caracteres em utf-8, prefixo `$2b$`).

**Se você está começando do zero (v1.1 fresh):**

Simplesmente rode o `schema.sql`. Ele já cria a tabela com
`VARCHAR(255)` para a coluna `senha`.

**Se você já tem o banco em produção (v0.x → v1.1 direto):**

A coluna atual provavelmente é `VARCHAR(64)` ou menor. Como **não é
possível converter hashes bcrypt de volta em senhas em claro**, você
precisa recadastrar todos os usuários.

```sql
-- 1. Backup de segurança
mysqldump -u root -p flowlog > backup_pre_bcrypt.sql

-- 2. Ajustar a coluna
ALTER TABLE usuarios MODIFY senha VARCHAR(255) NOT NULL;

-- 3. Limpar usuários existentes (TODOS serão perdidos)
TRUNCATE TABLE usuarios;

-- 4. Rodar a migration v1.0 → v1.1
mysql -u root -p flowlog < migrations/v1.0_to_v1.1.sql

-- 5. Recadastrar via menu do sistema, ou inserir manualmente:
--    O hash bcrypt é gerado por: bcrypt.hashpw(senha, bcrypt.gensalt())
--    Insira o hash em utf-8 (ex: $2b$12$ABC...60chars...xyz)
```

> A partir desta versão, `verificar_senha()` recusa autenticar contas
> com senha em texto puro e registra um WARNING no log. Ou seja,
> **toda conta sem hash bcrypt será bloqueada** — o que é o
> comportamento desejado.

### 2. Banco tem que existir

O `database.py` carrega o nome do banco da variável `DB_NAME` no
`.env`. Garanta que o `.env` está configurado:

```dotenv
DB_HOST=localhost
DB_USER=flowlog_user
DB_PASSWORD=sua_senha_forte
DB_NAME=flowlog
```

### 3. Dependências

```bash
pip install -r requirements.txt
```

(mantido desde v1.0: `mysql-connector-python`, `python-dotenv`, `bcrypt`)

### 4. Teste rápido pós-migração

```bash
python -m py_compile src/*.py
python -c "from src.utils import validar_cnpj; print(validar_cnpj('11.222.333/0001-81'))"  # True
python -c "from src.utils import validar_cnpj; print(validar_cnpj('11.222.333/0001-00'))"  # False
```

Se algum `py_compile` reclamar, copie a mensagem e abra uma issue.

---

## Resumo das migrations SQL

| Versão de origem | Versão destino | Arquivo                                | Mudanças no schema                  |
|------------------|----------------|----------------------------------------|-------------------------------------|
| (nenhuma)        | v1.1           | `schema.sql` (do começo ao fim)         | Setup completo                      |
| v1.0             | v1.1           | `migrations/v1.0_to_v1.1.sql`          | `+usuario_id` em `historico_movimentacoes` |
| v0.x             | v1.1           | `MIGRATION.md` (seção "v1.0 recap") + `migrations/v1.0_to_v1.1.sql` | `senha` redimensionada + `+usuario_id` |
