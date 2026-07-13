-- ============================================================
-- FlowLog — Migração v1.5 → v1.6
-- ============================================================
-- Adiciona:
--   - Tabela `empresas` (multi-filial / multi-CNPJ)
--   - Tabela `usuarios_empresas` (N:N usuário ↔ empresa com nível)
--   - Coluna `empresa_id` em produtos, fornecedores,
--     historico_movimentacoes, produtos_historico_edicoes
--   - Tabela `auditoria_acoes` (audit log avançado)
-- Migra dados existentes pra empresa "Padrão" (id=1).
--
-- Aplicação:
--   mysql -u root -p flowlog < migrations/v1.5_to_v1.6.sql
--
-- Rollback (manual): ver migrations/v1.6_to_v1.5.sql
-- ============================================================

USE flowlog;

START TRANSACTION;

-- ============================================================
-- 1. Tabela empresas
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

-- Empresa padrão (sempre presente, agrupa dados legados)
INSERT INTO empresas (id, cnpj, razao_social, nome_fantasia)
VALUES (1, '00000000000000', 'Empresa Padrão (legado v1.5)', 'Padrão')
ON DUPLICATE KEY UPDATE razao_social = VALUES(razao_social);

-- ============================================================
-- 2. Tabela usuarios_empresas (N:N)
-- ============================================================
CREATE TABLE IF NOT EXISTS usuarios_empresas (
    usuario_id    INT     NOT NULL,
    empresa_id    INT     NOT NULL,
    nivel_empresa TINYINT NOT NULL,  -- 1, 2 ou 3 (mesma escala do nivel_acesso)
    PRIMARY KEY (usuario_id, empresa_id),
    CONSTRAINT fk_ue_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ue_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_nivel_empresa CHECK (nivel_empresa IN (1, 2, 3))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Migra usuários existentes: cada um vira admin (nível 3) da empresa padrão
INSERT INTO usuarios_empresas (usuario_id, empresa_id, nivel_empresa)
SELECT u.id, 1, u.nivel_acesso
FROM usuarios u
ON DUPLICATE KEY UPDATE nivel_empresa = VALUES(nivel_empresa);

-- ============================================================
-- 3. Adiciona empresa_id em produtos
-- ============================================================
-- Primeiro adiciona como NULL (dados legados ainda sem empresa)
ALTER TABLE produtos
    ADD COLUMN empresa_id INT NULL AFTER id,
    ADD CONSTRAINT fk_produtos_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        ON DELETE RESTRICT ON UPDATE CASCADE;

UPDATE produtos SET empresa_id = 1 WHERE empresa_id IS NULL;

ALTER TABLE produtos MODIFY COLUMN empresa_id INT NOT NULL;
CREATE INDEX idx_produtos_empresa ON produtos (empresa_id, nome);

-- ============================================================
-- 4. Adiciona empresa_id em fornecedores
-- ============================================================
ALTER TABLE fornecedores
    ADD COLUMN empresa_id INT NULL AFTER id,
    ADD CONSTRAINT fk_fornecedores_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        ON DELETE RESTRICT ON UPDATE CASCADE;

UPDATE fornecedores SET empresa_id = 1 WHERE empresa_id IS NULL;

ALTER TABLE fornecedores MODIFY COLUMN empresa_id INT NOT NULL;
CREATE INDEX idx_fornecedores_empresa ON fornecedores (empresa_id, razao_social);

-- ============================================================
-- 5. Adiciona empresa_id em historico_movimentacoes
-- ============================================================
ALTER TABLE historico_movimentacoes
    ADD COLUMN empresa_id INT NULL AFTER produto_id,
    ADD CONSTRAINT fk_historico_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        ON DELETE RESTRICT ON UPDATE CASCADE;

UPDATE historico_movimentacoes h
JOIN produtos p ON p.id = h.produto_id
SET h.empresa_id = p.empresa_id
WHERE h.empresa_id IS NULL;

ALTER TABLE historico_movimentacoes MODIFY COLUMN empresa_id INT NOT NULL;
CREATE INDEX idx_historico_empresa ON historico_movimentacoes (empresa_id, data_movimentacao DESC);

-- ============================================================
-- 6. Adiciona empresa_id em produtos_historico_edicoes
-- ============================================================
ALTER TABLE produtos_historico_edicoes
    ADD COLUMN empresa_id INT NULL AFTER produto_id,
    ADD CONSTRAINT fk_hist_edit_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        ON DELETE CASCADE ON UPDATE CASCADE;

UPDATE produtos_historico_edicoes e
JOIN produtos p ON p.id = e.produto_id
SET e.empresa_id = p.empresa_id
WHERE e.empresa_id IS NULL;

ALTER TABLE produtos_historico_edicoes MODIFY COLUMN empresa_id INT NOT NULL;
CREATE INDEX idx_hist_edit_empresa ON produtos_historico_edicoes (empresa_id, data_edicao DESC);

-- ============================================================
-- 7. Tabela auditoria_acoes (audit log avançado)
-- ============================================================
CREATE TABLE IF NOT EXISTS auditoria_acoes (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id   INT     NULL,  -- NULL se ação do sistema
    empresa_id   INT     NULL,  -- NULL se ação global
    acao         VARCHAR(64)  NOT NULL,  -- 'CREATE', 'UPDATE', 'DELETE', 'LOGIN', etc.
    recurso      VARCHAR(64)  NOT NULL,  -- 'produto', 'fornecedor', 'usuario', etc.
    recurso_id   INT          NULL,      -- ID do recurso afetado
    ip           VARCHAR(45)  NULL,      -- IPv4 ou IPv6
    user_agent   VARCHAR(255) NULL,      -- User-Agent (pra API/CLI)
    payload      JSON         NULL,      -- Dados extras (antes/depois, params, etc.)
    criado_em    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_audit_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_audit_empresa FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_audit_usuario ON auditoria_acoes (usuario_id, criado_em DESC);
CREATE INDEX idx_audit_empresa ON auditoria_acoes (empresa_id, criado_em DESC);
CREATE INDEX idx_audit_recurso ON auditoria_acoes (recurso, recurso_id, criado_em DESC);
CREATE INDEX idx_audit_acao ON auditoria_acoes (acao, criado_em DESC);

-- ============================================================
-- 8. Configuração de retenção do audit log
-- ============================================================
CREATE TABLE IF NOT EXISTS config_sistema (
    chave   VARCHAR(64)  PRIMARY KEY,
    valor   TEXT         NOT NULL,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO config_sistema (chave, valor) VALUES
    ('audit_retencao_dias', '365'),
    ('audit_max_por_recurso', '1000')
ON DUPLICATE KEY UPDATE valor = VALUES(valor);

COMMIT;

-- ============================================================
-- Verificações pós-migração
-- ============================================================
-- Rode estas queries pra garantir que a migração deu certo:
--
-- SELECT COUNT(*) AS total_empresas FROM empresas;
--   (esperado: 1, a "Empresa Padrão")
--
-- SELECT COUNT(*) FROM produtos WHERE empresa_id IS NULL;
--   (esperado: 0)
--
-- SELECT COUNT(*) AS usuarios_sem_empresa
--   FROM usuarios u
--   LEFT JOIN usuarios_empresas ue ON ue.usuario_id = u.id
--   WHERE ue.usuario_id IS NULL;
--   (esperado: 0)

SELECT 'v1.5 → v1.6 migration OK' AS status;
