-- migrate:up
DROP INDEX IF EXISTS codes_upsert_constraint_idx;

ALTER TABLE conditions_codes ADD COLUMN source TEXT DEFAULT '' NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS code_system_source_constraint_idx
    ON conditions_codes (condition_id, code_id, source);

-- migrate:down
DROP INDEX IF EXISTS code_system_source_constraint_idx;

CREATE UNIQUE INDEX IF NOT EXISTS codes_upsert_constraint_idx
    ON codes (system_id, code);

ALTER TABLE conditions_codes DROP COLUMN source;

