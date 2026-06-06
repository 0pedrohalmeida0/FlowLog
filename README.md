# FlowLog - Gestão de Inventário

<p align="center">
  <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python" />
  <img src="https://img.shields.io/badge/mysql-%2300f.svg?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL" />
  <img src="https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white" alt="Git" />
</p>

## 🇺🇸 English Version

FlowLog is a robust inventory control system developed in Python and integrated with a MySQL database. Focused on logistical efficiency, the system automates stock tracking, balance validations, and movement auditing directly through the terminal.

### Current Features
* **Centralized Main Menu:** An intuitive terminal interface for seamless navigation between all system modules.
* **Product Management:** Interactive registration and detailed physical inventory listing.
* **Smart Stock Outflow:** Processes inventory pull-outs with automatic balance verification, preventing negative stock levels.
* **Critical Stock Alert:** Automatic notification triggered on system startup for items with fewer than 5 units in stock.
* **Movement History (Logs):** Detailed tracking of every outbound transaction, utilizing SQL table relationships (`JOIN`) for analytical auditing.
* **Data Security:** Implementation of environment variables (`.env`) for credentials management and strict defense against *SQL Injection*.

### Technologies Used
* **Language:** Python 3.x
* **Database:** MySQL
* **Connectivity:** `mysql-connector-python`
* **Environment Configuration:** `python-dotenv`

## 🇧🇷 Versão em Português

O FlowLog é um sistema de controle de estoque robusto desenvolvido em Python com integração ao banco de dados MySQL. Focado em eficiência logística, o sistema automatiza o rastreio de mercadorias, validações de saldo e auditoria de movimentações diretamente pelo terminal.

### Funcionalidades Atuais
* **Menu Principal Centralizado:** Interface intuitiva via terminal para navegação fluida entre todas as ferramentas do sistema.
* **Gestão de Produtos:** Cadastro interativo e listagem detalhada do inventário físico.
* **Saída de Estoque Inteligente:** Realiza baixas no inventário com verificação automática de saldo, impedindo estoque negativo.
* **Alerta de Estoque Crítico:** Notificação automática logo na inicialização para itens com menos de 5 unidades.
* **Histórico de Movimentações (Logs):** Registro detalhado de cada saída, utilizando relacionamentos de tabelas (`JOIN`) para auditoria analítica.
* **Segurança de Dados:** Implementação de variáveis de ambiente (`.env`) para credenciais e proteção rigorosa contra *SQL Injection*.

### Tecnologias Utilizadas
* **Linguagem:** Python 3.x
* **Banco de Dados:** MySQL
* **Conectividade:** `mysql-connector-python`
* **Configuração de Ambiente:** `python-dotenv`
