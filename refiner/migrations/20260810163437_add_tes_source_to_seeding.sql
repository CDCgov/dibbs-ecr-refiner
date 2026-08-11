-- migrate:up
DROP INDEX IF EXISTS codes_upsert_constraint_idx;

CREATE INDEX IF NOT EXISTS idx_conditions_tes_id 
    ON conditions (tes_id);

ALTER TABLE conditions_codes ADD COLUMN source_url TEXT DEFAULT '' NOT NULL;
ALTER TABLE conditions_codes ADD COLUMN source_name TEXT DEFAULT '';

CREATE UNIQUE INDEX IF NOT EXISTS code_system_source_constraint_idx
    ON conditions_codes (condition_id, code_id, source_url);

ALTER TABLE conditions_codes DROP CONSTRAINT conditions_codes_pkey;

ALTER TABLE conditions_codes ADD CONSTRAINT conditions_codes_source_pkey
    PRIMARY KEY (condition_id, code_id, source_url);

-- migrate:down
DROP INDEX IF EXISTS code_system_source_constraint_idx;
DROP INDEX IF EXISTS idx_conditions_tes_id;

ALTER TABLE conditions_codes DROP CONSTRAINT conditions_codes_source_pkey;

ALTER TABLE conditions_codes ADD CONSTRAINT conditions_codes_pkey
    PRIMARY KEY (condition_id, code_id);

CREATE UNIQUE INDEX IF NOT EXISTS codes_upsert_constraint_idx
    ON codes (system_id, code);

ALTER TABLE conditions_codes DROP COLUMN source_name;
ALTER TABLE conditions_codes DROP COLUMN source_url;
