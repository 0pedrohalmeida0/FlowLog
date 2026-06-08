# FlowLog - Gestão de Inventário

<p align="center">
  <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python" />
  <img src="https://img.shields.io/badge/mysql-%2300f.svg?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL" />
  <img src="https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white" alt="Git" />
</p>

## 🇺🇸 English Version

FlowLog is a robust inventory control system developed in Python and integrated with a MySQL database. Focused on logistical efficiency, the system automates stock tracking, balance validations, and movement auditing directly through the terminal.

### Current Features
* **Role-Based Access Control (RBAC):** Three-tier hierarchical security system (Operator, Manager, IT Admin) with secure authentication and restricted action permissions.
* **Centralized Main Menu:** An intuitive terminal interface for seamless navigation between all system modules.
* **Product & Supplier Management:** Interactive registration, physical inventory listing, and supplier-specific product filtering with automated CNPJ formatting.
* **Smart Inbound & Outbound Logistics:** Processes stock entries and pull-outs using strictly ID-based tracking, with automatic balance verification to prevent negative stock.
* **Dynamic Movement Auditing (Logs):** Detailed tracking of every transaction (Entries and Exits). Includes case-insensitive dynamic reporting and SQL `JOIN`s for analytical auditing.
* **Critical Stock Alert:** Automatic notification triggered on system startup for items with fewer than 5 units in stock.
* **Data Security:** Implementation of environment variables (`.env`) for credentials management and strict defense against *SQL Injection*.

### Technologies Used
* **Language:** Python 3.x
* **Database:** MySQL
* **Connectivity:** `mysql-connector-python`
* **Environment Configuration:** `python-dotenv`

## 🇧🇷 Versão em Português

O FlowLog é um sistema de controle de estoque robusto desenvolvido em Python com integração ao banco de dados MySQL. Focado em eficiência logística, o sistema automatiza o rastreio de mercadorias, validações de saldo e auditoria de movimentações diretamente pelo terminal.

### Funcionalidades Atuais
* **Controle de Acesso Hierárquico (RBAC):** Sistema de segurança em três níveis (Operador, Gerência, Admin TI) com login obrigatório e bloqueio de telas por permissão de usuário.
* **Menu Principal Centralizado:** Interface intuitiva via terminal para navegação fluida entre todas as ferramentas do sistema.
* **Gestão de Produtos e Fornecedores:** Cadastro interativo, listagem física e filtro de produtos por fornecedor com formatação automatizada de CNPJ (limpeza de caracteres).
* **Logística Inteligente de Entrada e Saída:** Processamento de recebimentos e baixas utilizando rastreio rígido por ID, com verificação matemática para impedir saldo negativo.
* **Auditoria Dinâmica de Movimentações (Logs):** Registro e extrato filtrável de Entradas e Saídas, blindado contra erros de digitação (busca *case-insensitive*) utilizando relacionamentos SQL (`JOIN`).
* **Alerta de Estoque Crítico:** Notificação automática logo na inicialização para itens com menos de 5 unidades.
* **Segurança de Dados:** Implementação de variáveis de ambiente (`.env`) para credenciais e proteção rigorosa contra *SQL Injection*.

### Tecnologias Utilizadas
* **Linguagem:** Python 3.x
* **Banco de Dados:** MySQL
* **Conectividade:** `mysql-connector-python`
* **Configuração de Ambiente:** `python-dotenv`
