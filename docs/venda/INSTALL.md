# 📦 Como instalar o FlowLog

> **Tempo estimado:** 5-10 minutos (com MySQL já instalado).
> **Pré-requisito:** Windows 10/11, MySQL 5.7+ ou MariaDB 10.3+.

## Instalação passo a passo

### 1. Baixe o instalador

Baixe `FlowLog_Setup_v1.5.0.exe` na [página de Releases](https://github.com/0pedrohalmeida0/FlowLog/releases/latest).

### 2. Rode o instalador

Duplo-clique no `.exe`. O wizard vai:

- Pedir pra aceitar a EULA
- Perguntar onde instalar (`C:\Program Files\FlowLog` é o padrão)
- Perguntar se quer ícone no desktop
- Perguntar se quer adicionar `flowlog` ao PATH do Windows

### 3. Instale o MySQL (se ainda não tem)

Se você ainda não tem MySQL rodando, escolha uma opção:

- **Mais fácil**: instale o [MySQL Community Server](https://dev.mysql.com/downloads/mysql/) com o MySQL Installer. Marque "Server only" pra ficar leve.
- **Alternativa dev**: instale o [XAMPP](https://www.apachefriends.org/) (vem com MySQL + Apache + PHP, mas você só vai usar o MySQL).
- **Docker** (avançado): `docker run -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=suasenha mysql:8`

### 4. Rode o Setup Wizard

Na primeira vez que abrir o FlowLog, ele vai rodar o **Setup Wizard**:

```
👋 Bem-vindo ao FlowLog! É a primeira vez que você roda.
Vamos configurar em 5 passos rápidos.
```

Ele vai pedir:

1. **Host do MySQL** (`localhost` se instalou local)
2. **Porta** (`3306` padrão)
3. **Usuário** (`root` se for dev local)
4. **Senha** (a que você definiu na instalação do MySQL)
5. **Nome do banco** (`flowlog` é o padrão, pode usar outro)

Depois ele testa a conexão, cria as tabelas, e cria um admin user. Você pode usar `admin / admin123` ou definir outro.

### 5. Comece a usar!

Login com o admin criado, e você verá o menu principal. **Trial de 30 dias** começa automaticamente.

---

## 🔄 Atualizando

Quando sair uma versão nova, o FlowLog mostra um aviso no startup:

```
🆕 Nova versão disponível: v1.5.1
   https://github.com/0pedrohalmeida0/FlowLog/releases/tag/v1.5.1
```

Você pode:

- Baixar manualmente o instalador novo e rodar por cima (mantém `.env` e banco)
- Ignorar e continuar usando a versão atual (sem prazo)
- Desativar update checks com `FLOWLOG_AUTO_UPDATE=0` no `.env`

## 🗑️ Desinstalando

**Opção 1**: Painel de Controle → Programas → FlowLog → Desinstalar

**Opção 2**: Menu Iniciar → FlowLog → Desinstalar FlowLog

**ATENÇÃO**: a desinstalação **NÃO** remove seu banco MySQL. Se quiser limpar tudo, rode:

```sql
DROP DATABASE flowlog;
```

E remova o diretório `%APPDATA%\FlowLog` (configurações e licença local).

---

## 🆘 Problemas comuns

### "Can't connect to MySQL server"

- MySQL não está rodando. Inicie: `net start mysql` (Windows) ou `sudo systemctl start mysql` (Linux).
- Firewall bloqueando a porta 3306.

### "Access denied for user"

- Senha errada. Recrie: `ALTER USER 'root'@'localhost' IDENTIFIED BY 'novasenha';`

### "Unknown database 'flowlog'"

- Setup wizard não rodou, ou o banco foi deletado. Rode `flowlog --setup` pra configurar de novo.

### "Port 3306 is already in use"

- Outra instância do MySQL está rodando, ou outra app usando a porta. Mude a porta do MySQL ou do FlowLog.

---

## 🐧 Instalando em Linux (avançado)

```bash
# 1. Clonar o repo
git clone https://github.com/0pedrohalmeida0/FlowLog.git
cd FlowLog

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Setup wizard
python -m src.setup_wizard

# 4. Rodar
python -m src
```

Ou empacotar como `.AppImage` com PyInstaller (configuração manual; entre em contato pra versão oficial).

---

## 📞 Suporte

- Issues: https://github.com/0pedrohalmeida0/FlowLog/issues
- Email: contato@flowlog.app
- Documentação completa: [README.md](../../README.md) + [ROADMAP.md](../../ROADMAP.md)
