-- migrate:up
-- 1. Drop the legacy index
DROP INDEX IF EXISTS idx_conditions_child_snomed_codes;

-- 2. Drop the legacy column
ALTER TABLE conditions DROP COLUMN IF EXISTS child_rsg_snomed_codes;

-- migrate:down
-- Since dropping a column is destructive, we cannot easily restore the data
-- without a backup. We will leave the down migration empty or implement a
-- basic column restoration if the schema allows.
ALTER TABLE conditions ADD COLUMN child_rsg_snomed_codes TEXT[];
CREATE INDEX idx_conditions_child_snomed_codes ON conditions USING GIN (child_rsg_snomed_codes);
