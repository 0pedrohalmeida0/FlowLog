# ✨ Features do FlowLog Licença

> Tudo o que está incluído na versão **FlowLog Licença** (on-premise, instalável).
> Para features **exclusivas do FlowLog Cloud** (SaaS), veja [ROADMAP.md](../../ROADMAP.md#diferenciais-exclusivos-por-sku-princípio-estratégico).

---

## 🛡️ Segurança (de fábrica)

- **Autenticação bcrypt** — senhas armazenadas com hash bcrypt + pré-normalização SHA-256 (aceita qualquer tamanho, suporta Unicode)
- **Bloqueio de conta** — 5 tentativas falhas → bloqueio por 15 min
- **Auto-logout** — 30 min de inatividade → encerra sessão
- **RBAC hierárquico** — 3 níveis: Operador (1), Gerente (2), Admin TI (3)
- **Sanitização de logs** — senhas, host e user são removidos de mensagens de erro do MySQL antes de logar
- **Senha do MySQL via env var** — backup não expõe senha em `ps aux` (vai como `MYSQL_PWD`)
- **CSV injection mitigation** — nomes de produto com `=`, `+`, `-`, `@` são sanitizados (CVE-2014-3524)
- **SQL parametrizado 100%** — zero risco de SQL injection

## 📦 Gestão de inventário

- **Cadastro de produtos** com nome, quantidade, preço de custo, fornecedor, alerta mínimo, data de entrada
- **Edição de produtos** — nome, preço, alerta (quantidade só via entrada/saída, com histórico)
- **Listagem paginada** — 50 produtos por tela, configurável
- **Busca por fornecedor** — filtra produtos de um CNPJ específico
- **Alerta de estoque crítico** — notificação no startup + sugestão de compra (`qtd_sugerida = max(alerta * 2 - atual, 0)`)
- **Fornecedores** com validação de CNPJ (rejeita dígitos Unicode, sequências repetidas, DVs errados)

## 📊 Relatórios

- **Curva ABC (Pareto)** — classifica produtos em A/B/C com base no volume de saída. Janela SQL `SUM() OVER (ORDER BY ...)` — performance nativa do banco
- **Histórico de movimentações** — paginado, filtrável (Entradas / Saídas / Todas), com ano no formato
- **Inventário atual** — listagem em tela ou export CSV
- **Export para CSV** — UTF-8 com BOM, separador `;`, padrão Excel BR. Inclui watermark se em trial

## 🔄 Movimentação

- **Entrada de estoque** com transação atômica (`SELECT ... FOR UPDATE`)
- **Saída (baixa)** com validação de estoque disponível
- **Histórico completo** de toda movimentação, com FK para usuário (`quem fez`)
- **Edição auditada** — snapshot JSON antes/depois de cada mudança em `produtos_historico_edicoes`

## 🔌 Importação / Exportação

- **Import CSV de produtos** em massa — UTF-8 com ou sem BOM, separador `;` ou `,`, decimais `.` ou `,`
- **Export CSV** de inventário, histórico e Curva ABC
- **Validação linha a linha** — pula inválidas, mostra resumo no final
- **Limite de 50 MB** por arquivo (anti-OOM)
- **Dedup automático de fornecedores** — CNPJs repetidos no mesmo CSV usam o mesmo fornecedor (sem UNIQUE error)

## 💾 Backup e restauração

- **Backup via mysqldump** — `mysqldump`/`mysql` direto do Python
- **Retenção configurável** (`BACKUP_MAX_RETENTION`, default 30)
- **Senha via env var** (não em argv)
- **Restore com confirmação** — exige digitar "RESTAURAR"

## 🌐 API REST local (v1.6)

- **FastAPI** sob o mesmo processo: `/api/produtos`, `/api/movimentacoes`, `/api/relatorios`
- **OpenAPI/Swagger UI** em `/docs`
- **Autenticação por API key** (escopo: read-only, read-write, admin)
- **Rate limit** por token
- **Webhooks** para eventos críticos (`estoque.critico`, `backup.concluido`)
- **Para integração com ERP local** — não exposto à internet

## 🏢 Multi-filial (v1.6)

- **Vários CNPJs numa instalação** — schema `empresas` + `usuarios_empresas` (N:N)
- **RBAC granular por empresa** — usuário pode ser admin na Filial A e operador na B
- **Troca de contexto** — usuário escolhe qual filial está operando
- **Isolamento total** — toda query filtra por `empresa_id`

## 🔐 SSO / LDAP (v1.6)

- **Active Directory** e **OpenLDAP** suportados
- **Opcional e configurável** — pode coexistir com autenticação local
- **Mapeamento de grupos** para níveis RBAC

## 📋 Audit log avançado (v1.6)

- **Tabela `auditoria_acoes`** separada do histórico de estoque
- **Registra**: usuário, IP, user-agent, ação, payload, timestamp
- **Retenção configurável** (default 365 dias)
- **Exportável** para CSV ou SIEM externo

## 📈 Dashboard de métricas (v1.6)

- **Web** em `/admin/metrics` (Chart.js)
- **5+ gráficos**: produtos mais vendidos, evolução de estoque, alertas por mês, top fornecedores
- **Refresh em < 5s**

## 🎨 White-label (v1.6)

- **Logo, cores e nome do cliente** no relatório exportado (PDF/CSV)
- **Identidade visual customizada** por tenant

## 💻 Operação

- **CLI intuitiva** com menu numerado
- **Trial de 30 dias** automático no primeiro start
- **Sistema de licença** com chave HMAC (não precisa de servidor externo pra validar)
- **Setup wizard** no primeiro start (5 passos: EULA, MySQL, schema, admin, trial)
- **Auto-update** via GitHub Releases (aviso no startup, sem forçar)
- **i18n** PT-BR + EN (configurável via `FLOWLOG_LANG`)

## 🐧 Compatibilidade

- **Windows 10/11** (64-bit) — instalador oficial
- **Linux** (qualquer distro) — `pip install` + run manual
- **macOS** — `pip install` + run manual (sem instalador oficial ainda)
- **MySQL 5.7+ / 8.x** e **MariaDB 10.3+**

---

## ❌ O que **NÃO** está no FlowLog Licença

(Para saber o que está no Cloud, veja o [ROADMAP.md](../../ROADMAP.md#diferenciais-exclusivos-por-sku-princípio-estratégico).)

- **Mobile / PWA** — só no Cloud
- **Integrações Zapier/Make/Slack** — só no Cloud
- **IA (previsão de demanda)** — só no Cloud
- **Self-service signup** — só no Cloud
- **White-label completo pra revenda** — só no Cloud

Se você precisa de qualquer um desses, considere o [FlowLog Cloud](https://flowlog.app/cloud).
