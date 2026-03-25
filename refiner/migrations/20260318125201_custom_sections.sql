-- migrate:up

ALTER TYPE event_type_enum
    ADD VALUE IF NOT EXISTS 'create_custom_section';

ALTER TYPE event_type_enum
    ADD VALUE IF NOT EXISTS 'edit_custom_section';

ALTER TYPE event_type_enum
    ADD VALUE IF NOT EXISTS 'delete_custom_section';

CREATE TYPE configurations_sections_type AS ENUM (
    'standard',
    'custom'
);

ALTER TABLE configurations_sections
    ADD COLUMN section_type configurations_sections_type;

-- backfill data
UPDATE configurations_sections
SET section_type = 'standard'
WHERE section_type IS NULL;


ALTER TABLE configurations_sections
    ALTER COLUMN section_type SET NOT NULL;

ALTER TABLE configurations_sections
    ADD CONSTRAINT configurations_sections_configuration_id_name_key
    UNIQUE (configuration_id, name);

-- migrate:down

ALTER TABLE configurations_sections
    DROP CONSTRAINT IF EXISTS configurations_sections_configuration_id_name_key;

ALTER TABLE configurations_sections
    DROP COLUMN IF EXISTS section_type;

DROP TYPE IF EXISTS configurations_sections_type;
