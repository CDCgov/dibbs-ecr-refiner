-- migrate:up
ALTER TABLE configurations
ADD COLUMN original_condition_id UUID REFERENCES conditions(id);

-- Backfill original_condition_id from primary condition
UPDATE configurations c
SET original_condition_id = cc.condition_id
FROM configurations_conditions cc
WHERE c.id = cc.configuration_id
  AND cc.is_primary = true
  AND c.original_condition_id IS NULL;

-- If no primary condition exists, set to first associated condition
UPDATE configurations c
SET original_condition_id = (
    SELECT cc.condition_id
    FROM configurations_conditions cc
    WHERE cc.configuration_id = c.id
    LIMIT 1
)
WHERE c.original_condition_id IS NULL;

-- migrate:down
-- Revert backfill: set original_condition_id to NULL where it was backfilled
-- Note: This is a data migration that cannot be perfectly reversed without
-- tracking the original state. Setting to NULL is acceptable.
UPDATE configurations
SET original_condition_id = NULL
WHERE original_condition_id IS NOT NULL;

ALTER TABLE configurations
DROP COLUMN original_condition_id;
