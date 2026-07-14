-- migrate:up
-- 1. Final data migration (JSONB ➡️ Join Table) for any remaining records.
-- This ensures that any data entered in the legacy column during the transition period
-- is captured in the new normalized structure.

INSERT INTO codes (code, system_id, version, display)
SELECT DISTINCT
    unnest(child_rsg_snomed_codes),
    (SELECT id FROM systems WHERE key = 'snomed'),
    '6.0.0',
    'Migrated Code'
FROM conditions
WHERE child_rsg_snomed_codes IS NOT NULL
ON CONFLICT (system_id, version, code) DO NOTHING;

INSERT INTO conditions_rsg_codes (condition_id, code_id)
SELECT
    c.id,
    co.id
FROM conditions c
CROSS JOIN LATERAL unnest(c.child_rsg_snomed_codes) AS code_val
JOIN codes co ON co.code = code_val AND co.system_id = (SELECT id FROM systems WHERE key = 'snomed')
WHERE c.child_rsg_snomed_codes IS NOT NULL
ON CONFLICT (condition_id, code_id) DO NOTHING;

-- 2. Drop the legacy index
DROP INDEX IF EXISTS idx_conditions_child_snomed_codes;

-- 3. Drop the legacy column
ALTER TABLE conditions DROP COLUMN IF EXISTS child_rsg_snomed_codes;

-- migrate:down
-- Since dropping a column is destructive, we cannot easily restore the data
-- without a backup. We will leave the down migration empty or implement a
-- basic column restoration if the schema allows.
ALTER TABLE conditions ADD COLUMN child_rsg_snomed_codes TEXT[];
CREATE INDEX idx_conditions_child_snomed_codes ON conditions USING GIN (child_rsg_snomed_codes);
