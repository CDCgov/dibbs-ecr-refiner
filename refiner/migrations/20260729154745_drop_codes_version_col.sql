-- migrate:up
-- Replace the unique constraint to scope to the existing codes
ALTER TABLE codes
    DROP CONSTRAINT IF EXISTS codes_system_id_version_value_key;

ALTER TABLE codes
    DROP COLUMN version;

-- delete rows made duplicate with the dropped version so we can apply the 
-- followup unique index

WITH duplicates_to_delete AS (
    DELETE FROM codes c1
    USING codes c2
    WHERE c1.id > c2.id
      AND c1.system_id = c2.system_id
      AND c1.code = c2.code
    RETURNING c1.id AS old_id, c2.id AS new_id
)
UPDATE conditions_codes cc
SET cc.code_id = d.new_id
FROM duplicates_to_delete d
WHERE cc.code_id = d.old_id;

ALTER TABLE codes
    ADD CONSTRAINT codes_system_id_code_value_key
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
      DENSE_RANK() OVER (PARTITION BY cc.code_id ORDER BY tes.version ASC) as rn
    FROM conditions_codes cc 
    JOIN codes c ON cc.code_id = c.id 
    JOIN conditions cond ON cc.condition_id = cond.id 
    JOIN tes ON cond.tes_id = tes.id
)
UPDATE codes c 
SET version = rv.version 
FROM ranked_codes rv 
WHERE c.id = rv.code_id AND rv.rn = 1;

-- Rebuild the old constraint
ALTER TABLE codes
    DROP CONSTRAINT IF EXISTS codes_system_id_code_value_key,
    ALTER COLUMN version SET NOT NULL,
    ADD CONSTRAINT codes_system_id_version_value_key
        UNIQUE (system_id, version, code);

-- -- -- insert all the other ones
INSERT INTO codes (system_id, code, version, display, created_at)
SELECT
    c.system_id,
    c.code,
    t.version,
    c.display,
    c.created_at
FROM conditions_codes cc
LEFT JOIN codes c ON c.id = cc.code_id 
LEFT JOIN conditions cond ON cc.condition_id = cond.id
LEFT JOIN tes t ON cond.tes_id = t.id 
ON CONFLICT (system_id, version, code) DO NOTHING;
