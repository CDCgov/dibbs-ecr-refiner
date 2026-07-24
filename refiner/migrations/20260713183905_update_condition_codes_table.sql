-- migrate:up
ALTER TABLE conditions_rsg_codes RENAME TO conditions_codes;
ALTER TABLE conditions_codes ADD COLUMN is_child_rsg BOOLEAN DEFAULT FALSE;
CREATE UNIQUE INDEX IF NOT EXISTS codes_upsert_constraint_idx 
    ON codes (system_id, version, code);

-- migrate:down
ALTER TABLE condition_codes DROP COLUMN is_child_rsg;
ALTER TABLE conditions_codes RENAME TO conditions_rsg_codes;
