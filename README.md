# 📦 FlowLog - Gestão de Inventário

O **FlowLog** é um sistema de controle de estoque robusto desenvolvido em Python com integração ao banco de dados MySQL. Focado em eficiência logística, o sistema automatiza o rastreio de mercadorias, validações de saldo e auditoria de movimentações diretamente pelo terminal.

## 🚀 Funcionalidades Atuais

- **Menu Principal Centralizado:** Interface intuitiva para navegação entre todas as ferramentas do sistema.
- **Gestão de Produtos:** Cadastro interativo e listagem detalhada do inventário.
- **Saída de Estoque Inteligente:** Realiza baixas no inventário com verificação automática de saldo (impede estoque negativo).
- **Alerta de Estoque Crítico:** Notificação automática logo na inicialização para itens com menos de 5 unidades.
- **Histórico de Movimentações (Logs):** Registro detalhado de cada saída, utilizando relacionamentos de tabelas (JOIN) para auditoria.
- **Segurança de Dados:** Implementação de variáveis de ambiente (`.env`) e proteção contra SQL Injection.

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** [Python 3.x](https://www.python.org/)
- **Banco de Dados:** [MySQL](https://www.mysql.com/)
- **Conectividade:** `mysql-connector-python`
- **Configuração:** `python-dotenv`

## 📂 Estrutura do Projeto

```text
FlowLog/
├── src/
│   ├── main.py                # Ponto de entrada e menu do sistema
│   ├── database.py            # Gerenciamento da conexão com MySQL
│   ├── cadastro_interativo.py  # Interface de entrada de novos produtos
│   ├── saida_estoque.py       # Lógica de baixa e atualização de saldo
│   ├── listar_produtos.py     # Relatórios de inventário e lógica de alertas
│   ├── ver_historico.py       # Consulta ao log de movimentações (JOIN SQL)
│   └── utils.py               # Funções auxiliares e registro de logs
├── .env                       # Configurações sensíveis (DB_HOST, DB_USER, etc.)
└── requirements.txt           # Dependências para instalação
