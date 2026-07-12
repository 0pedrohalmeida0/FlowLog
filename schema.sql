-- ============================================================
-- FlowLog - Schema do banco de dados
-- ============================================================
-- MySQL 5.7+ / 8.x
-- Charset: utf8mb4 (suporte completo a Unicode)
-- ============================================================

CREATE DATABASE IF NOT EXISTS flowlog
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE flowlog;

-- ============================================================
-- Tabela: usuarios
-- ============================================================
-- A coluna `senha` foi dimensionada para VARCHAR(255) para acomodar
-- o hash bcrypt (60 caracteres em utf-8) com folga para upgrades
-- futuros (argon2, scrypt, etc.).
-- Senhas em texto puro NÃO são mais aceitas (ver MIGRATION.md).
-- ============================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(64)  NOT NULL UNIQUE,
    senha         VARCHAR(255) NOT NULL,           -- bcrypt hash ($2b$...)
    nivel_acesso  TINYINT      NOT NULL,           -- 1=Operador, 2=Gerente, 3=Admin
    criado_em     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_nivel CHECK (nivel_acesso IN (1, 2, 3))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Tabela: fornecedores
-- ============================================================
-- O CNPJ é armazenado SEM máscara (apenas dígitos). A busca
-- por fornecedor normaliza a entrada via REPLACE() no SQL para
-- também aceitar valores com máscara.
-- ============================================================
CREATE TABLE IF NOT EXISTS fornecedores (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    razao_social   VARCHAR(255) NOT NULL,
    cnpj           VARCHAR(14)  NOT NULL UNIQUE,    -- apenas dígitos
    criado_em      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_fornecedores_cnpj ON fornecedores(cnpj);

-- ============================================================
-- Tabela: produtos
-- ============================================================
-- `alerta_minimo` NULL significa "sem alerta configurado".
-- Quando preenchido, a função alerta_estoque_baixo() compara
-- quantidade <= alerta_minimo.
-- ============================================================
CREATE TABLE IF NOT EXISTS produtos (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nome            VARCHAR(255)  NOT NULL,
    quantidade      INT           NOT NULL DEFAULT 0,
    preco_custo     DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    fornecedor_id   INT           NULL,
    alerta_minimo   INT           NULL,
    data_entrada    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_produtos_fornecedor
        FOREIGN KEY (fornecedor_id) REFERENCES fornecedores(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_quantidade  CHECK (quantidade    >= 0),
    CONSTRAINT chk_preco       CHECK (preco_custo   >= 0),
    CONSTRAINT chk_alerta      CHECK (alerta_minimo IS NULL OR alerta_minimo >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_produtos_fornecedor ON produtos(fornecedor_id);
CREATE INDEX idx_produtos_alerta    ON produtos(quantidade, alerta_minimo);

-- ============================================================
-- Tabela: historico_movimentacoes
-- ============================================================
-- Registra toda entrada e saída. ATENÇÃO: recomendo adicionar a
-- coluna usuario_id (FK para usuarios) na próxima migração, para
-- fechar o requisito de auditoria (ver MIGRATION.md).
-- ============================================================
CREATE TABLE IF NOT EXISTS historico_movimentacoes (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    produto_id        INT           NOT NULL,
    tipo              VARCHAR(10)   NOT NULL,    -- 'ENTRADA' ou 'SAIDA'
    quantidade        INT           NOT NULL,
    data_movimentacao DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_historico_produto
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_tipo       CHECK (tipo IN ('ENTRADA', 'SAIDA')),
    CONSTRAINT chk_qtd_hist   CHECK (quantidade > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_historico_produto ON historico_movimentacoes(produto_id);
CREATE INDEX idx_historico_data   ON historico_movimentacoes(data_movimentacao DESC);
CREATE INDEX idx_historico_tipo   ON historico_movimentacoes(tipo);
