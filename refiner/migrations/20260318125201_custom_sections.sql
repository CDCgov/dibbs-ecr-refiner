-- migrate:up
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

-- migrate:down
ALTER TABLE configurations_sections
    DROP COLUMN IF EXISTS section_type;

DROP TYPE IF EXISTS configurations_sections_type;
