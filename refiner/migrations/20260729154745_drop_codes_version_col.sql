-- migrate:up

CREATE INDEX IF NOT EXISTS idx_conditions_codes_code_id
    ON conditions_codes (code_id);

CREATE INDEX IF NOT EXISTS idx_conditions_codes_condition_id
    ON conditions_codes (condition_id);

-- Replace the unique constraint to scope to the existing codes
ALTER TABLE codes
    DROP CONSTRAINT IF EXISTS codes_system_id_version_value_key;

-- replace rows in the join table with the deconflicted ID's and then
-- delete rows made duplicate with the dropped version so we can apply the
-- followup unique index. Tiebreak self join by version so the replacement
-- ids line up.
WITH duplicates_to_delete AS (
    DELETE FROM codes c1
    USING codes c2
    WHERE c1.version > c2.version
      AND c1.system_id = c2.system_id
      AND c1.code = c2.code
    RETURNING c1.id AS new_id, c2.id AS old_id
)
UPDATE conditions_codes
SET code_id = d.old_id
FROM duplicates_to_delete d
WHERE code_id = d.new_id;

ALTER TABLE codes
    DROP COLUMN version;

ALTER TABLE codes
    ADD CONSTRAINT codes_system_id_code_value_key
        UNIQUE (system_id, code);

-- migrate:down

DROP INDEX IF EXISTS idx_conditions_codes_code_id;
DROP INDEX IF EXISTS idx_conditions_codes_condition_id;

-- Re-add version column
ALTER TABLE codes
    ADD COLUMN version text;

-- Rebuild the version column on the codes table

-- set the existing code version columns to the highest RV code
WITH ranked_codes AS (
    SELECT
      c.id as code_id,
      tes.version,
      ROW_NUMBER() OVER (PARTITION BY cc.code_id ORDER BY tes.version ASC) as rn
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

-- update the join table with all the re-inserted codes by checking the linked
-- TES version
UPDATE conditions_codes cc
SET code_id = new_codes.id
FROM
    conditions cond,
    tes t,
    codes new_codes,
    codes old_codes
WHERE cc.condition_id = cond.id
    AND cond.tes_id = t.id
    AND cc.code_id = old_codes.id
    AND old_codes.code = new_codes.code
    AND old_codes.system_id = new_codes.system_id
    AND new_codes.version = t.version
    AND cc.code_id != new_codes.id;
