-- migrate:up
ALTER TABLE conditions_context_groupers RENAME COLUMN name TO display_name;
ALTER TABLE conditions_context_groupers ADD COLUMN parent_url TEXT;
ALTER TABLE conditions_context_groupers RENAME TO conditions_valuesets;

ALTER TABLE conditions_codes
    DROP CONSTRAINT IF EXISTS conditions_codes_pkey;

ALTER TABLE conditions_codes
    ADD COLUMN valueset_id UUID,
    ADD CONSTRAINT fk_conditions_valuesets_fkey
    FOREIGN KEY (valueset_id)
    REFERENCES conditions_valuesets (id)
    ON DELETE CASCADE;

-- migrate:down
ALTER TABLE conditions_codes
    DROP CONSTRAINT IF EXISTS fk_conditions_valuesets_fkey;

ALTER TABLE conditions_codes DROP COLUMN valueset_id;

ALTER TABLE conditions_valuesets RENAME COLUMN display_name TO name;
ALTER TABLE conditions_valuesets DROP COLUMN parent_url;
ALTER TABLE conditions_valuesets RENAME TO conditions_context_groupers;
