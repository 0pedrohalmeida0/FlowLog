-- ============================================================
-- Migration: v1.0 → v1.1
-- ============================================================
-- Adiciona a coluna usuario_id em historico_movimentacoes,
-- permitindo registrar QUEM fez cada movimentação.
--
-- Como aplicar:
--   mysql -u root -p flowlog < migrations/v1.0_to_v1.1.sql
--
-- Observações:
-- - A coluna é adicionada como NULL, não NOT NULL: linhas
--   legadas (criadas antes desta migration) permanecem válidas.
-- - A query de relatório usa LEFT JOIN com a tabela usuarios e
--   exibe "(sistema)" quando o username for NULL, então não há
--   quebra de funcionalidade.
-- - O ON DELETE SET NULL garante que, se um usuário for excluído
--   do banco, o histórico de movimentações dele permanece —
--   apenas perdemos a referência ao nome.
-- ============================================================

USE flowlog;

ALTER TABLE historico_movimentacoes
    ADD COLUMN usuario_id INT NULL AFTER quantidade,
    ADD CONSTRAINT fk_historico_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE SET NULL ON UPDATE CASCADE;

CREATE INDEX idx_historico_usuario ON historico_movimentacoes(usuario_id);
