-- migrate:up

-- create the join table
CREATE TABLE configurations_conditions (
    configuration_id UUID NOT NULL REFERENCES configurations(id) ON DELETE CASCADE,
    condition_id UUID NOT NULL REFERENCES conditions(id) ON DELETE CASCADE,
    PRIMARY KEY (configuration_id, condition_id)
);

-- migrate existing data from the array column
INSERT INTO configurations_conditions (configuration_id, condition_id)
SELECT id, unnest(included_conditions)
FROM configurations
WHERE included_conditions <> '{}';

-- drop the old column
ALTER TABLE configurations
    DROP COLUMN included_conditions;

-- migrate:down

-- restore the column
ALTER TABLE configurations
    ADD COLUMN included_conditions UUID[] NOT NULL DEFAULT '{}';

-- repopulate from the join table
UPDATE configurations c
SET included_conditions = sub.condition_ids
FROM (
    SELECT configuration_id, array_agg(condition_id) AS condition_ids
    FROM configurations_conditions
    GROUP BY configuration_id
) sub
WHERE c.id = sub.configuration_id;

-- drop the join table
DROP TABLE configurations_conditions;
