-- ============================================================
-- FlowLog — migration: v1.1 → v1.2
-- ============================================================
-- Adiciona bloqueio de conta após tentativas falhas de login.
--
-- Como aplicar:
--   mysql -u root -p flowlog < migrations/v1.1_to_v1.2.sql
-- ============================================================

USE flowlog;

ALTER TABLE usuarios
    ADD COLUMN tentativas_falhas INT NOT NULL DEFAULT 0 AFTER nivel_acesso,
    ADD COLUMN bloqueado_ate     DATETIME NULL AFTER tentativas_falhas;

CREATE INDEX idx_usuarios_bloqueado_ate ON usuarios(bloqueado_ate);
