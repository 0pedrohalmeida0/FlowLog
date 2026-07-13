-- ============================================================
-- FlowLog - Schema do banco de dados (v1.6)
-- ============================================================
-- MySQL 5.7+ / 8.x
-- Charset: utf8mb4 (suporte completo a Unicode)
--
-- Fresh install: rode este arquivo do começo ao fim.
-- Atualização de v1.0: migrations/v1.0_to_v1.1.sql
-- Atualização de v1.5: migrations/v1.5_to_v1.6.sql (multi-filial + audit)
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
-- Tabela: empresas (v1.6 — multi-filial / multi-CNPJ)
-- ============================================================
-- Cada empresa é um CNPJ distinto. Dados de produtos, fornecedores
-- e movimentações são isolados por empresa_id. Usuários podem ter
-- níveis diferentes em empresas diferentes (N:N).
-- ============================================================
CREATE TABLE IF NOT EXISTS empresas (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    cnpj            VARCHAR(14)  NOT NULL UNIQUE,
    razao_social    VARCHAR(255) NOT NULL,
    nome_fantasia   VARCHAR(255),
    ativa           BOOLEAN      NOT NULL DEFAULT TRUE,
    criado_em       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_cnpj_len CHECK (LENGTH(cnpj) = 14)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS usuarios_empresas (
    usuario_id    INT     NOT NULL,
    empresa_id    INT     NOT NULL,
    nivel_empresa TINYINT NOT NULL,  -- 1, 2 ou 3
    PRIMARY KEY (usuario_id, empresa_id),
    CONSTRAINT fk_ue_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ue_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_nivel_empresa CHECK (nivel_empresa IN (1, 2, 3))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_usuarios_empresas_usuario ON usuarios_empresas (usuario_id);
CREATE INDEX idx_usuarios_empresas_empresa ON usuarios_empresas (empresa_id);

-- ============================================================
-- Tabela: fornecedores
-- ============================================================
-- O CNPJ é armazenado SEM máscara (apenas dígitos). A busca
-- por fornecedor normaliza a entrada via REPLACE() no SQL para
-- também aceitar valores com máscara.
-- ============================================================
CREATE TABLE IF NOT EXISTS fornecedores (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id     INT          NOT NULL,  -- v1.6: multi-filial
    razao_social   VARCHAR(255) NOT NULL,
    cnpj           VARCHAR(14)  NOT NULL,    -- apenas dígitos (único por empresa)
    criado_em      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_fornecedores_empresa_cnpj (empresa_id, cnpj),
    CONSTRAINT fk_fornecedores_empresa
        FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_fornecedores_cnpj ON fornecedores(cnpj);
CREATE INDEX idx_fornecedores_empresa ON fornecedores(empresa_id, razao_social);

-- ============================================================
-- Tabela: produtos
-- ============================================================
-- `alerta_minimo` NULL significa "sem alerta configurado".
-- Quando preenchido, a função alerta_estoque_baixo() compara
-- quantidade <= alerta_minimo.
-- ============================================================
CREATE TABLE IF NOT EXISTS produtos (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id      INT           NOT NULL,  -- v1.6: multi-filial
    nome            VARCHAR(255)  NOT NULL,
    quantidade      INT           NOT NULL DEFAULT 0,
    preco_custo     DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    fornecedor_id   INT           NULL,
    alerta_minimo   INT           NULL,
    data_entrada    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_produtos_fornecedor
        FOREIGN KEY (fornecedor_id) REFERENCES fornecedores(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_produtos_empresa
        FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_quantidade  CHECK (quantidade    >= 0),
    CONSTRAINT chk_preco       CHECK (preco_custo   >= 0),
    CONSTRAINT chk_alerta      CHECK (alerta_minimo IS NULL OR alerta_minimo >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_produtos_fornecedor ON produtos(fornecedor_id);
CREATE INDEX idx_produtos_alerta    ON produtos(quantidade, alerta_minimo);
CREATE INDEX idx_produtos_empresa    ON produtos(empresa_id, nome);

-- ============================================================
-- Tabela: historico_movimentacoes
-- ============================================================
-- v1.1: agora cada linha registra QUEM fez a movimentação,
-- via FK para usuarios(id). Linhas antigas (sem usuario_id)
-- permanecem legíveis: a query usa LEFT JOIN e exibe "(sistema)"
-- para o username quando o campo é NULL.
-- ============================================================
CREATE TABLE IF NOT EXISTS historico_movimentacoes (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    produto_id        INT           NOT NULL,
    empresa_id        INT           NOT NULL,  -- v1.6: multi-filial
    tipo              VARCHAR(10)   NOT NULL,    -- 'ENTRADA' ou 'SAIDA'
    quantidade        INT           NOT NULL,
    data_movimentacao DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuario_id        INT           NULL,        -- v1.1: NULL = registro legado
    CONSTRAINT fk_historico_produto
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_historico_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_historico_empresa
        FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_tipo       CHECK (tipo IN ('ENTRADA', 'SAIDA')),
    CONSTRAINT chk_qtd_hist   CHECK (quantidade > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_historico_produto  ON historico_movimentacoes(produto_id);
CREATE INDEX idx_historico_data     ON historico_movimentacoes(data_movimentacao DESC);
CREATE INDEX idx_historico_tipo     ON historico_movimentacoes(tipo);
CREATE INDEX idx_historico_usuario  ON historico_movimentacoes(usuario_id);
CREATE INDEX idx_historico_empresa  ON historico_movimentacoes(empresa_id, data_movimentacao DESC);

-- ============================================================
-- Tabela: produtos_historico_edicoes (v1.3)
-- ============================================================
-- Snapshot JSON do produto antes e depois de cada edição.
-- Permite auditar "o que mudou, por quem e quando" sem
-- precisar de uma coluna por campo (que quebraria a cada
-- nova coluna em `produtos`).
-- ============================================================
CREATE TABLE IF NOT EXISTS produtos_historico_edicoes (
    id              INT  AUTO_INCREMENT PRIMARY KEY,
    produto_id      INT  NOT NULL,
    empresa_id      INT  NOT NULL,  -- v1.6: multi-filial
    usuario_id      INT  NULL,
    snapshot_antes  JSON NOT NULL,
    snapshot_depois JSON NOT NULL,
    data_edicao     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_hist_edit_produto
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_hist_edit_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_hist_edit_empresa
        FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_hist_edit_produto ON produtos_historico_edicoes(produto_id);
CREATE INDEX idx_hist_edit_data    ON produtos_historico_edicoes(data_edicao DESC);
CREATE INDEX idx_hist_edit_usuario ON produtos_historico_edicoes(usuario_id);
CREATE INDEX idx_hist_edit_empresa ON produtos_historico_edicoes(empresa_id, data_edicao DESC);

-- ============================================================
-- Tabela: auditoria_acoes (v1.6 — audit log avançado)
-- ============================================================
-- Registra toda ação mutante: usuário, empresa, IP, user-agent,
-- ação, recurso, payload. Retenção configurável (default 365 dias,
-- via config_sistema).
-- ============================================================
CREATE TABLE IF NOT EXISTS auditoria_acoes (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id   INT          NULL,       -- NULL se ação do sistema
    empresa_id   INT          NULL,       -- NULL se ação global
    acao         VARCHAR(64)  NOT NULL,   -- 'CREATE', 'UPDATE', 'DELETE', 'LOGIN', etc.
    recurso      VARCHAR(64)  NOT NULL,   -- 'produto', 'fornecedor', 'usuario', etc.
    recurso_id   INT          NULL,
    ip           VARCHAR(45)  NULL,       -- IPv4 ou IPv6
    user_agent   VARCHAR(255) NULL,       -- User-Agent (pra API/CLI)
    payload      JSON         NULL,
    criado_em    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_audit_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_audit_usuario ON auditoria_acoes (usuario_id, criado_em DESC);
CREATE INDEX idx_audit_empresa ON auditoria_acoes (empresa_id, criado_em DESC);
CREATE INDEX idx_audit_recurso ON auditoria_acoes (recurso, recurso_id, criado_em DESC);
CREATE INDEX idx_audit_acao    ON auditoria_acoes (acao, criado_em DESC);

-- ============================================================
-- Tabela: config_sistema (v1.6 — configurações runtime)
-- ============================================================
-- Pares chave/valor editáveis pelo admin. Usado para retenção
-- de audit log, defaults de feature, etc.
-- ============================================================
CREATE TABLE IF NOT EXISTS config_sistema (
    chave         VARCHAR(64)  PRIMARY KEY,
    valor         TEXT         NOT NULL,
    atualizado_em DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO config_sistema (chave, valor) VALUES
    ('audit_retencao_dias', '365'),
    ('audit_max_por_recurso', '1000')
ON DUPLICATE KEY UPDATE valor = VALUES(valor);
