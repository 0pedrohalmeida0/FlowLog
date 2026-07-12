# Guia de Migração — bcrypt + transações atômicas

Esta versão do FlowLog traz três mudanças de infra que exigem ação
manual antes do primeiro start:

## 1. Senha agora é hash bcrypt

A coluna `senha` na tabela `usuarios` precisa estar dimensionada para
acomodar o hash bcrypt (60 caracteres em utf-8, prefixo `$2b$`).

### Se você está começando do zero

Simplesmente rode o `schema.sql` na raiz do projeto. Ele já cria a
tabela com `VARCHAR(255)` para a coluna `senha`.

```bash
mysql -u root -p < schema.sql
```

### Se você já tem o banco em produção

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

-- 4. Recadastrar via menu do sistema, ou inserir manualmente:
--    O hash bcrypt é gerado por: bcrypt.hashpw(senha, bcrypt.gensalt())
--    Insira o hash em utf-8 (ex: $2b$12$ABC...60chars...xyz)
```

> A partir desta versão, `verificar_senha()` recusa autenticar contas
> com senha em texto puro e exibe um aviso. Ou seja, **toda conta sem
> hash bcrypt será bloqueada** — o que é o comportamento desejado.

## 2. Banco tem que existir

O `database.py` carrega o nome do banco da variável `DB_NAME` no
`.env`. Garanta que o `.env` está configurado:

```dotenv
DB_HOST=localhost
DB_USER=flowlog_user
DB_PASSWORD=sua_senha_forte
DB_NAME=flowlog
```

Crie o banco (caso ainda não exista) rodando o `schema.sql`.

## 3. Dependência nova

Adicionada `bcrypt` ao `requirements.txt`. Instale/reinstale:

```bash
pip install -r requirements.txt
```

## 4. Mudanças de comportamento

| Onde                  | Antes                                | Agora                                                      |
|-----------------------|--------------------------------------|------------------------------------------------------------|
| `login.py`            | Senha em texto puro                  | Hash bcrypt; `getpass` para esconder a senha no terminal   |
| `entrada.py`          | UPDATE + INSERT em conexões separadas | Uma única transação atômica (commit/rollback consistentes) |
| `saida_estoque.py`    | UPDATE + INSERT em conexões separadas | Uma única transação atômica + `SELECT ... FOR UPDATE`      |
| `cadastro_interativo` | Loop com código morto após `break`   | Loop limpo; valida CNPJ; insere `alerta_minimo`            |
| `ver_historico.py`    | `f-string` montando SQL              | Query parametrizada via dicionário de constantes           |
| `utils.py`            | `registrar_log(id, tipo, qtd)`       | `registrar_log(cursor, id, tipo, qtd)` — usa o cursor do chamador (transação) |
| CNPJ em qualquer entrada | Só limpava caracteres              | Valida dígitos verificadores antes de gravar               |

## 5. Próximas migrações recomendadas (não incluídas)

Estas não estão neste patch, mas viram débito técnico rápido. Anote:

- **Adicionar `usuario_id` em `historico_movimentacoes`** — sem isso
  não dá pra responder "quem registrou a saída X". Cria a coluna,
  popula retroativamente se possível, e propaga nos INSERTs de log.
- **Bloqueio de conta após N tentativas falhas** — tabela
  `tentativas_login` ou coluna `bloqueado_ate` em `usuarios`.
- **Edição de produto** — hoje só dá pra excluir + recriar, o que
  quebra a referência do histórico.

## 6. Teste rápido pós-migração

```bash
python -m py_compile src/*.py
python -c "from src.utils import validar_cnpj; print(validar_cnpj('11.222.333/0001-81'))"  # True
python -c "from src.utils import validar_cnpj; print(validar_cnpj('11.222.333/0001-00'))"  # False
```

Se algum `py_compile` reclamar, copie a mensagem e me manda.
