-- ============================================================
-- FlowLog — migration: v1.2 → v1.3
-- ============================================================
-- Adiciona histórico de edições de produto (snapshot antes/depois).
--
-- Como aplicar:
--   mysql -u root -p flowlog < migrations/v1.2_to_v1.3.sql
-- ============================================================

USE flowlog;

CREATE TABLE IF NOT EXISTS produtos_historico_edicoes (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    produto_id    INT  NOT NULL,
    usuario_id    INT  NULL,
    -- Snapshot JSON do produto ANTES da edição.
    -- Usar JSON (e não colunas por campo) deixa a tabela flexível
    -- para futuras colunas em `produtos` sem migração de histórico.
    snapshot_antes JSON NOT NULL,
    -- Snapshot JSON do produto DEPOIS da edição.
    snapshot_depois JSON NOT NULL,
    data_edicao   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_hist_edit_produto
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_hist_edit_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_hist_edit_produto ON produtos_historico_edicoes(produto_id);
CREATE INDEX idx_hist_edit_data    ON produtos_historico_edicoes(data_edicao DESC);
CREATE INDEX idx_hist_edit_usuario ON produtos_historico_edicoes(usuario_id);
