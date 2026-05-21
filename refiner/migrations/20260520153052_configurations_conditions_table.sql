-- migrate:up

CREATE TABLE configurations_conditions (
    configuration_id UUID NOT NULL REFERENCES configurations(id) ON DELETE CASCADE,
    condition_id UUID NOT NULL REFERENCES conditions(id) ON DELETE CASCADE,
    is_primary BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY (configuration_id, condition_id)
);

-- only allow one primary condition per configuration
CREATE UNIQUE INDEX one_primary_per_configuration
ON configurations_conditions (configuration_id)
WHERE is_primary = true;

-- migrate existing data. condition_id is the primary value
INSERT INTO configurations_conditions (configuration_id, condition_id, is_primary)
SELECT
    id,
    unnest(included_conditions),
    unnest(included_conditions) = condition_id  -- true if it matches the primary condition ID
FROM configurations
WHERE included_conditions <> '{}';

-- drop the old columns
ALTER TABLE configurations
    DROP COLUMN included_conditions,
    DROP COLUMN condition_id CASCADE, -- this will delete: `configurations_condition_id_not_null`, `configurations_set_condition_canonical_url_trigger`, `configurations_condition_id_fkey`
    DROP COLUMN condition_canonical_url; -- use canonical_url on the condition instead

-- migrate:down

-- restore the columns first
ALTER TABLE configurations
    ADD COLUMN condition_id UUID,
    ADD COLUMN included_conditions UUID[] NOT NULL DEFAULT '{}',
    ADD COLUMN condition_canonical_url TEXT;

-- repopulate from the join table while it still exists
UPDATE configurations c
SET
    condition_id = sub.primary_condition_id,
    included_conditions = sub.condition_ids
FROM (
    SELECT
        configuration_id,
        array_agg(condition_id) AS condition_ids,
        (
            SELECT condition_id FROM configurations_conditions cc2
            WHERE cc2.configuration_id = cc.configuration_id
            AND cc2.is_primary = true
            LIMIT 1
        ) AS primary_condition_id
    FROM configurations_conditions cc
    GROUP BY configuration_id
) sub
WHERE c.id = sub.configuration_id;

-- repopulate condition_canonical_url from conditions
UPDATE configurations c
SET condition_canonical_url = cond.canonical_url
FROM conditions cond
WHERE cond.id = c.condition_id;

-- drop new join table
DROP TABLE configurations_conditions;

-- restore NOT NULL and FK constraints on condition_id
ALTER TABLE configurations
    ALTER COLUMN condition_id SET NOT NULL,
    ADD CONSTRAINT configurations_condition_id_fkey FOREIGN KEY (condition_id) REFERENCES conditions(id);
