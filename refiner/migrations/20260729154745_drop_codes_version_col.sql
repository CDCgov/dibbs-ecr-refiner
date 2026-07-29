-- migrate:up
ALTER TABLE codes
    DROP COLUMN version;

-- Replace the unique constraint to scope to the existing codes
ALTER TABLE codes
    DROP CONSTRAINT IF EXISTS codes_upsert_constraint_idx,
    ADD CONSTRAINT codes_upsert_constraint_idx
        UNIQUE (system_id, code);

-- migrate:down

-- Re-add version column
ALTER TABLE codes
    ADD COLUMN version text NOT NULL;

-- Rebuild the version column on the codes table
UPDATE codes c
SET version = (
    SELECT t.version
    FROM conditions_codes cc 
    JOIN conditions cond ON cc.condition_id = cond.id
    JOIN tes t ON cond.tes_id = t.id
    WHERE cc.code_id = c.id
);

-- Rebuild the old constraint
ALTER TABLE custom_codes
    DROP CONSTRAINT IF EXISTS codes_upsert_constraint_idx,
    ADD CONSTRAINT codes_upsert_constraint_idx
        UNIQUE (system_id, version, code);

