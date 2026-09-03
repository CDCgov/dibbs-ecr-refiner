-- migrate:up
ALTER TABLE conditions_codes_temp ADD COLUMN is_trigger_code BOOLEAN NOT NULL DEFAULT FALSE;

-- migrate:down
ALTER TABLE conditions_codes_temp DROP COLUMN is_trigger_code;
