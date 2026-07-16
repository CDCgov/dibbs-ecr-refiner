-- migrate:up

-- Add configuration_id to custom_codes table
ALTER TABLE custom_codes
    ADD COLUMN configuration_id UUID REFERENCES configurations(id);

-- Replace the unique constraint to scope it per configuration
ALTER TABLE custom_codes
    DROP CONSTRAINT IF EXISTS custom_codes_system_id_value_key,
    ADD CONSTRAINT custom_codes_configuration_id_system_id_code_key
        UNIQUE (configuration_id, system_id, code);

-- Insert existing jsonb custom_codes data into the custom_codes table,
-- map system_key -> system_id using systems table
INSERT INTO custom_codes (display, code, system_id, configuration_id)
SELECT
    cc->>'name'    AS display,
    cc->>'code'    AS code,
    s.id           AS system_id,
    c.id           AS configuration_id
FROM
    configurations c,
    jsonb_array_elements(c.custom_codes) AS cc
    JOIN systems s ON s.key = cc->>'system_key';

-- Drop jsonb column from configurations
ALTER TABLE configurations
    DROP COLUMN custom_codes;


-- migrate:down

-- Re-add the jsonb column
ALTER TABLE configurations
    ADD COLUMN custom_codes jsonb;

-- Rebuild the JSONB array on each configuration from the custom_codes table rows
UPDATE configurations c
SET custom_codes = (
    SELECT jsonb_agg(
        jsonb_build_object(
            'code',       cc.code,
            'name',       cc.display,
            'system_key', s.key
        )
    )
    FROM custom_codes cc
    JOIN systems s ON s.id = cc.system_id
    WHERE cc.configuration_id = c.id
);

-- Remove rows that were migrated from the jsonb column
DELETE FROM custom_codes WHERE configuration_id IS NOT NULL;

-- Drop new constraint
ALTER TABLE custom_codes
    DROP CONSTRAINT IF EXISTS custom_codes_configuration_id_system_id_code_key;

-- Drop new column
ALTER TABLE custom_codes
    DROP COLUMN IF EXISTS configuration_id;
