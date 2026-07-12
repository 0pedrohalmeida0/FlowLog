# 📋 FlowLog Updates

> Release notes e changelog oficial do projeto. Este documento acompanha cada nova versão, comunicando **o que mudou**, **por que mudou** e **o que fazer para atualizar** uma instalação existente.
>
> *Official release notes and changelog. This document tracks every new version, communicating **what changed**, **why it changed**, and **how to upgrade** an existing installation.*

---

## v1.0 — 12 de julho de 2026

> *"De protótipo para produto — segurança, integridade e profissionalismo de ponta a ponta."*
> *"From prototype to product — end-to-end security, integrity, and professionalism."*

---

### 🇧🇷 Versão em Português

#### ✨ Destaques desta versão

Esta release marca um salto de qualidade do FlowLog. O sistema sai de um estágio de protótipo funcional e entra em um patamar de **produto com fundamentos sólidos de segurança e integridade de dados**. Tudo o que está aqui é resultado de uma revisão criteriosa do código, pensando em quem vai colocar o sistema em produção amanhã.

**Em uma frase:** as senhas dos usuários agora são protegidas com criptografia industrial, e cada movimentação de estoque acontece como uma operação única e atômica — se algo falhar, nada fica pela metade.

#### 🔒 Segurança reforçada

- **Criptografia de senhas com bcrypt.** As senhas são armazenadas com bcrypt, o mesmo padrão usado por bancos e aplicações que levam segurança a sério. Mesmo que alguém tivesse acesso direto ao banco de dados, não conseguiria ler as senhas em formato utilizável. *(Nota técnica: o sistema recusa autenticar contas com senha em texto puro — todos os usuários precisarão ser recadastrados na migração.)*
- **Senha invisível durante o login.** Ao autenticar, a senha agora é digitada de forma oculta, como em qualquer sistema profissional. Quem está ao lado não vê mais os caracteres sendo digitados.
- **Validação rigorosa de CNPJ.** O sistema agora verifica os dígitos verificadores do CNPJ antes de cadastrar um fornecedor. CNPJs digitados errado, incompletos ou inválidos são barrados na hora — sem mais lixo no banco de dados.

#### ⚡ Integridade de dados

- **Transações atômicas em entradas e saídas.** Quando você registra uma saída de estoque, duas coisas precisam acontecer: o saldo do produto diminui **e** o histórico é gravado. Antes, essas duas operações podiam falhar de forma independente, deixando o sistema com saldo divergente do histórico. Agora, ou as duas acontecem, ou nenhuma acontece. **O cenário "estoque mudou mas o log sumiu" deixou de existir.**
- **Proteção contra concorrência.** O sistema agora trava a linha do produto durante uma operação de entrada ou saída, evitando que dois usuários registrando movimentos ao mesmo tempo gerem saldos errados. *(Cobertura técnica: `SELECT ... FOR UPDATE`.)*
- **Filtro de histórico blindado.** O relatório de movimentações foi reescrito para impedir injeção de SQL via parâmetros de filtro — uma camada extra de proteção que elimina um risco que existia (ainda que teórico) no código anterior.

#### 🛠️ Operação e instalação

- **Schema SQL documentado.** Pela primeira vez, o FlowLog tem um `schema.sql` formal, com tabelas, índices, chaves estrangeiras e *constraints* (CHECK de quantidade não-negativa, faixas válidas para nível de acesso, etc.). Subir o banco do zero virou um único comando.
- **Guia de migração passo a passo.** O `MIGRATION.md` explica exatamente o que fazer para atualizar uma instalação existente: backup, ajuste de coluna, recadastro de usuários e testes de aceitação.

#### 📊 Antes e depois

| Aspecto                 | Antes                                        | Agora                                                |
|-------------------------|----------------------------------------------|------------------------------------------------------|
| Senha no banco          | Texto puro                                   | Hash bcrypt (`$2b$`, 60 caracteres)                  |
| Senha no terminal       | Visível ao digitar                           | Invisível (`getpass`)                                |
| Validação de CNPJ       | Só removia máscara                           | Verifica dígitos verificadores                      |
| Entrada/saída de estoque | Duas conexões separadas, podia quebrar no meio | Uma transação atômica (commit/rollback consistentes) |
| Saídas simultâneas      | Race condition (risco de saldo errado)       | Linha travada durante a operação                     |
| Criação do banco        | Manual, sem documentação                     | `schema.sql` pronto, com índices e *constraints*     |
| Atualização de versão   | Sem documentação                             | `MIGRATION.md` com checklist completo                |

#### 📋 O que muda para instalações existentes

> ⚠️ **Atenção:** se você já tem o FlowLog em uso, esta versão exige uma migração manual. O processo completo está em `MIGRATION.md`. O ponto principal é: **todos os usuários precisarão ser recadastrados**, porque o sistema não consegue converter senhas antigas (em texto puro) para o novo formato bcrypt — e isso é proposital, é assim que funciona criptografia boa.

Em resumo, para atualizar:

1. Faça backup do banco de dados.
2. Rode o novo `schema.sql` (ou aplique o `ALTER TABLE` documentado).
3. Atualize as dependências (`pip install -r requirements.txt`, que agora inclui `bcrypt`).
4. Substitua os arquivos de `src/`.
5. Recadastre os usuários.
6. Rode os testes de aceitação descritos em `MIGRATION.md`.

#### 🚀 Próximas entregas (preview)

- 👤 **Auditoria completa** — o sistema vai registrar *quem* fez cada movimentação, não só *o quê*.
- 🔐 **Bloqueio de conta** após tentativas falhas de login.
- ✏️ **Edição de produtos** (hoje só é possível excluir e recadastrar).
- 📦 **Instalador gráfico** para Windows, com PyInstaller + Inno Setup.

---

### 🇺🇸 English Version

#### ✨ Highlights of this release

This release marks a quality leap for FlowLog. The system leaves the "functional prototype" stage and steps into the level of a **product with solid security and data integrity foundations**. Everything in this update is the result of a careful code review, with one thing in mind: anyone who wants to put the system in production tomorrow.

**In one sentence:** user passwords are now protected with industrial-grade encryption, and every stock movement happens as a single, atomic operation — if anything fails, nothing is left half-done.

#### 🔒 Strengthened security

- **Password encryption with bcrypt.** Passwords are now stored using bcrypt, the same standard used by banks and security-conscious applications. Even if someone had direct access to the database, they could not read the passwords in a usable form. *(Technical note: the system refuses to authenticate accounts with plaintext passwords — all users will need to be re-registered during the migration.)*
- **Hidden password at the terminal.** When logging in, the password is now typed invisibly, just like in any professional system. Anyone looking over your shoulder will no longer see the characters being typed.
- **Strict CNPJ validation.** The system now verifies the check digits of the CNPJ before registering a supplier. Mistyped, incomplete, or otherwise invalid CNPJs are blocked on the spot — no more garbage in the database.

#### ⚡ Data integrity

- **Atomic transactions on inbound and outbound.** When you record an outbound movement, two things need to happen: the product's stock decreases **and** the history is logged. Previously, those two operations could fail independently, leaving the system with a stock balance that diverged from the history. Now, either both happen, or neither does. **The "stock changed but the log vanished" scenario no longer exists.**
- **Concurrency protection.** The system now locks the product row during an inbound or outbound operation, preventing two users recording movements at the same time from creating incorrect balances. *(Under the hood: `SELECT ... FOR UPDATE`.)*
- **Hardened history filter.** The movements report has been rewritten to prevent SQL injection through filter parameters — an extra protection layer that eliminates a (theoretical, but real) risk in the previous code.

#### 🛠️ Operations and installation

- **Documented SQL schema.** For the first time, FlowLog ships with a formal `schema.sql`, including tables, indexes, foreign keys, and constraints (CHECK for non-negative stock, valid access level ranges, etc.). Setting up the database from scratch is now a single command.
- **Step-by-step migration guide.** `MIGRATION.md` explains exactly what to do to upgrade an existing installation: backup, column adjustment, user re-registration, and acceptance tests.

#### 📊 Before and after

| Aspect                  | Before                                          | Now                                                  |
|-------------------------|-------------------------------------------------|------------------------------------------------------|
| Password in database    | Plain text                                      | bcrypt hash (`$2b$`, 60 characters)                  |
| Password at terminal    | Visible while typing                            | Hidden (`getpass`)                                   |
| CNPJ validation         | Only removed the mask                           | Verifies check digits                                |
| Inbound/outbound stock  | Two separate connections, could fail mid-way    | One atomic transaction (consistent commit/rollback)   |
| Concurrent movements    | Race condition (risk of wrong balance)          | Row locked during the operation                      |
| Database creation       | Manual, undocumented                            | Ready-to-use `schema.sql` with indexes & constraints |
| Version upgrade         | No documentation                                | `MIGRATION.md` with a complete checklist             |

#### 📋 What changes for existing installations

> ⚠️ **Attention:** if you already have FlowLog in use, this version requires a manual migration. The complete process is documented in `MIGRATION.md`. The key point is: **all users will need to be re-registered**, because the system cannot convert old (plaintext) passwords to the new bcrypt format — and that's by design. That's how good encryption works.

In short, to upgrade:

1. Back up the database.
2. Run the new `schema.sql` (or apply the documented `ALTER TABLE`).
3. Update dependencies (`pip install -r requirements.txt`, which now includes `bcrypt`).
4. Replace the `src/` files.
5. Re-register the users.
6. Run the acceptance tests described in `MIGRATION.md`.

#### 🚀 Coming next (preview)

- 👤 **Full audit trail** — the system will record *who* made each movement, not just *what*.
- 🔐 **Account lockout** after failed login attempts.
- ✏️ **Product editing** (today you can only delete and re-register).
- 📦 **Graphical installer** for Windows, built with PyInstaller + Inno Setup.

---

<p align="center">
  <sub>
    Dúvidas ou problemas com a migração? Abra uma <em>issue</em> no repositório.<br>
    Questions or issues with the migration? Open an <em>issue</em> in the repository.
  </sub>
</p>
