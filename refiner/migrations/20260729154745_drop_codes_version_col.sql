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
    ADD COLUMN version text;

-- Rebuild the version column on the codes table

-- set the existing code version columns to the highest RV code
WITH ranked_codes AS (
    SELECT 
      c.id as code_id,
      tes.version,
      ROW_NUMBER() OVER (PARTITION BY c.id ORDER BY tes.version ASC) as rn 
    FROM conditions_codes cc 
    JOIN codes c ON cc.code_id = c.id 
    JOIN conditions cond ON cc.condition_id = cond.id 
    JOIN tes ON cond.tes_id = tes.id
)
UPDATE codes c 
SET version = rv.version 
FROM ranked_codes rv 
WHERE c.id = rv.code_id AND rv.rn = 1;

-- -- insert all the other ones
-- INSERT INTO codes (system_id, code, version, display, created_at)
-- SELECT 
--     c.system_id,
--     c.code,
--     rv.version,
--     c.display,
--     c.created_at
-- FROM conditions_codes cc 
-- JOIN conditions cond ON cc.condition_id = cond.id 
-- JOIN tes ON cond.tes_id = tes.id
-- JOIN codes c ON c.id = cc.code_id
-- JOIN (
--     SELECT 
--       cc.code_id,
--       tes.version,
--       ROW_NUMBER() OVER (PARTITION BY cc.code_id ORDER BY tes.version ASC) as rn 
--     FROM conditions_codes cc 
--     JOIN conditions cond ON cc.condition_id = cond.id 
--     JOIN tes ON cond.tes_id = tes.id
-- ) rv ON rv.code_id = cc.code_id AND rv.version = tes.version 
-- WHERE rv.rn > 1
-- ON CONFLICT (system_id, codes) DO UPDATE SET 
--     version = EXCLUDED.version;

-- Rebuild the old constraint
ALTER TABLE codes
    DROP CONSTRAINT IF EXISTS codes_upsert_constraint_idx,
    -- ALTER COLUMN version SET NOT NULL,
    ADD CONSTRAINT codes_upsert_constraint_idx
        UNIQUE (system_id, version, code);

