# ❓ FAQ — Perguntas Frequentes

## Sobre o produto

### O que é o FlowLog?

Sistema de gestão de inventário com integridade de dados de nível bancário. Feito em Python + MySQL, operação 100% via terminal. Foco em pequenas e médias empresas que precisam de controle sério de estoque.

### Quais os pré-requisitos?

- Windows 10/11 (ou Linux/macOS com `pip install`)
- MySQL 5.7+ ou MariaDB 10.3+ (local ou em rede)
- 100 MB de espaço em disco
- 512 MB de RAM

### Funciona offline?

**Sim, total.** O FlowLog Licença é on-premise, então funciona sem internet. Útil para galpões, indústrias e lojas em zona rural.

### Funciona em rede local?

**Sim.** Vários terminais podem conectar ao mesmo banco MySQL. Cada terminal tem seu próprio `.env` apontando pro servidor.

### Suporta multi-filial?

**Sim** (a partir da v1.6). Uma instalação, vários CNPJs, com isolamento de dados por `empresa_id` e RBAC granular por filial.

### Tem versão web?

A versão on-premise (Licença) não. Para web, veja o [FlowLog Cloud](https://flowlog.app/cloud) (SaaS, cobrança mensal).

### Tem app mobile?

A versão Licença não. O Cloud tem PWA instalável no celular (a partir da v2.0).

### Tem API?

**Sim** (a partir da v1.6). API REST local via FastAPI, com OpenAPI/Swagger UI. Para integração com ERP local. **Não exposta à internet.**

### Quais integrações tem?

**On-premise**: NFe via certificado A1 local, ECF/SAT, balança, leitor de código de barras (hardware local).
**Cloud**: Zapier, Make, Slack, Google Sheets, NFe.io (a partir da v2.1).

---

## Sobre licenciamento e preço

### Quanto custa?

- **Licença vitalícia**: R$ XXX (one-time, 1 instalação)
- **Licença anual**: R$ YY/ano (com updates e suporte)
- **Trial gratuito**: 30 dias, sem cartão

Contato: contato@flowlog.app

### Como funciona o trial?

Ao instalar e rodar pela primeira vez, o trial de 30 dias começa automaticamente. Sem cadastro, sem cartão. Relatórios gerados durante o trial têm marca d'água "[FLOWLOG TRIAL — X dias restantes]".

### Como ativo a licença depois do trial?

Compre uma chave de ativação e rode:
```
flowlog --ativar XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
```

A chave é validada localmente (HMAC), não precisa de internet. A partir daí, a marca d'água sai dos relatórios e o sistema continua funcionando.

### O que acontece se o trial expirar e eu não ativar?

O sistema continua rodando, mas com a marca d'água nos relatórios. **Não bloqueia** o uso — é "honest system", não DRM agressivo.

### Posso instalar em várias máquinas?

Cada instalação (cada `license.json`) precisa de uma chave separada. Para multi-filial, todas as filiais podem usar a mesma chave se for a mesma empresa.

### Posso revender?

Sim, com o **programa de revenda** (entre em contato). White-label disponível na v1.6+.

### Tem desconto para ONG/educação?

Sim. Contato: contato@flowlog.app com comprovante.

---

## Sobre dados e backup

### Onde meus dados ficam?

No MySQL da sua empresa. Você tem controle total. O FlowLog Licença **não** envia dados para lugar nenhum.

### Como faço backup?

Opção 1 (recomendado): dentro do FlowLog, opção "Backup" no menu. Cria um `.sql` na pasta `backups/`.

Opção 2 (avançado): use o `mysqldump` do MySQL diretamente. Cron diário:
```bash
mysqldump -u root -pSENHA flowlog > backup_$(date +\%F).sql
```

### Como restauro?

Opção 1: dentro do FlowLog, opção "Restaurar backup".

Opção 2: linha de comando:
```bash
mysql -u root -pSENHA flowlog < backup_2026-07-12.sql
```

### Posso perder dados?

Se você fizer backup regularmente, não. **O FlowLog não substitui sua política de backup.** Recomendamos:
- Backup diário automático
- Manter últimos 30 backups (configurável)
- Testar restore periodicamente (a coisa mais importante)

### E se o MySQL cair?

O FlowLog não tem redundância. Se o MySQL cair, o sistema fica fora. Para alta disponibilidade, use:
- MySQL em cluster (replicação master-slave)
- Ou migre pro **FlowLog Cloud** (que tem SLA de 99.9%)

---

## Sobre segurança

### Quão seguro é o software?

- Senhas com **bcrypt** (work factor 12, ~250ms por hash)
- **Lockout** após 5 tentativas falhas
- **Auto-logout** após 30 min de inatividade
- Auditoria completa de edições (snapshot antes/depois)
- Audit log de ações (a partir da v1.6) com IP e user-agent

### Meus dados estão seguros?

Sim, **MAS** isso depende de você:
- Use senha forte no MySQL
- Não exponha a porta 3306 na internet
- Mantenha o sistema operacional atualizado
- Faça backups regulares

O FlowLog não vai te proteger de senha fraca no MySQL ou servidor desatualizado.

### Tem criptografia em repouso?

Não nativamente. Você pode habilitar **Transparent Data Encryption (TDE)** no MySQL Enterprise, ou criptografar o disco (BitLocker no Windows, LUKS no Linux).

### E LGPD?

O FlowLog armazena dados pessoais (nome de usuário). Para exclusão:
```sql
DELETE FROM usuarios WHERE id = X;
```

Logs de auditoria são anonimizados (não apagam) para manter trilha. Para deletar TUDO:
```sql
DROP DATABASE flowlog;
```

---

## Sobre suporte

### Tem suporte técnico?

- **Trial**: só comunidade (GitHub Issues)
- **Licença vitalícia**: 30 dias de email support na compra + comunidade depois
- **Licença anual**: email support + SLA 24h em horário comercial

### Tem treinamento?

Para licença anual, oferecemos 1h de onboarding por vídeo-chamada. Treinamentos adicionais sob contrato.

### Tem garantia de devolução?

Sim, 7 dias após a compra, sem perguntas. Reembolso integral se não gostar.

### E se eu encontrar um bug?

Abra uma issue: https://github.com/0pedrohalmeida0/FlowLog/issues. Resposta em até 48h em horário comercial (anual) ou quando der (vitalícia).

---

## Comparação com alternativas

### FlowLog vs. Excel

| | Excel | FlowLog |
|---|---|---|
| Auditoria de mudanças | ❌ | ✅ |
| Multi-usuário com lock | ❌ | ✅ |
| Alerta automático | ❌ | ✅ |
| Curva ABC | Manual | Automática |
| Backup versionado | ❌ | ✅ |
| API | ❌ | ✅ (v1.6) |
| Custo inicial | R$ 400+ | Trial grátis |

### FlowLog vs. ERP grande (SAP, TOTVS, etc.)

| | ERP grande | FlowLog |
|---|---|---|
| Preço inicial | R$ 50.000+ | Trial grátis |
| Tempo de implantação | 3-12 meses | < 1 dia |
| Customização | Equipe dedicada | Você mesmo (com código) |
| Suporte | SLA contratual | Comunidade / email |
| Escopo | Tudo (compras, vendas, fiscal, RH) | Estoque (e multi-filial) |
| Quando escolher | Empresa 100+ colaboradores com processos complexos | Empresa 1-50 colaboradores focada em inventário |

**Não tentamos ser um ERP completo.** Somos especializados em inventário, e por isso entregamos valor onde ERPs são genéricos demais.

### FlowLog Licença vs. FlowLog Cloud

| | Licença | Cloud |
|---|---|---|
| Preço | One-time R$X | Mensal R$Y |
| Onde roda | Sua máquina | Servidor nosso |
| Offline | ✅ | ❌ |
| Mobile | ❌ | ✅ (v2.0) |
| IA | ❌ | ✅ (v3.0) |
| Updates | Manual | Automático |
| Quando escolher | Quer controle total / dados próprios | Quer zero fricção / mobilidade |

---

## Não encontrou a resposta?

- 📧 Email: contato@flowlog.app
- 🐛 Issues: https://github.com/0pedrohalmeida0/FlowLog/issues
- 📖 Docs: [README.md](../../README.md) + [ROADMAP.md](../../ROADMAP.md)
