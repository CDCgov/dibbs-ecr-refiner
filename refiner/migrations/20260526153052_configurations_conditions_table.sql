-- migrate:up

-- create new join table
CREATE TABLE configurations_conditions (
    configuration_id UUID NOT NULL REFERENCES configurations(id) ON DELETE CASCADE,
    condition_id UUID NOT NULL REFERENCES conditions(id),
    is_primary BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY (configuration_id, condition_id)
);

-- only allow one primary condition per config
CREATE UNIQUE INDEX one_primary_per_configuration
ON configurations_conditions (configuration_id)
WHERE is_primary = true;

-- migrate existing data. condition_id is the primary value
INSERT INTO configurations_conditions (configuration_id, condition_id, is_primary)
SELECT DISTINCT -- avoid duplicates
    id,
    unnest(included_conditions),
    unnest(included_conditions) = condition_id
FROM configurations
WHERE included_conditions IS NOT NULL AND included_conditions <> '{}'
UNION
-- ensure the primary condition is always present, even if missing from included_conditions
SELECT id, condition_id, true
FROM configurations
WHERE condition_id IS NOT NULL
  AND NOT (condition_id = ANY(included_conditions))
ON CONFLICT (configuration_id, condition_id) DO UPDATE SET is_primary = true;

-- drop the old columns
ALTER TABLE configurations
    DROP COLUMN included_conditions,
    DROP COLUMN condition_id CASCADE, -- this will delete: `configurations_condition_id_not_null`, `configurations_set_condition_canonical_url_trigger`, `configurations_condition_id_fkey`
    DROP COLUMN condition_canonical_url;

-- drop the version trigger and function (versioning is now handled in the application layer)
DROP TRIGGER IF EXISTS configurations_set_version_on_insert ON configurations;
DROP FUNCTION IF EXISTS configurations_set_version_on_insert() CASCADE;

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

-- restore condition_canonical_url trigger for configs
CREATE FUNCTION configurations_set_condition_canonical_url_on_insert() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  -- grab canonical_url from conditions when inserting or updating condition_id
  SELECT canonical_url
  INTO NEW.condition_canonical_url
  FROM conditions
  WHERE id = NEW.condition_id
  LIMIT 1;

  RETURN NEW;
END;
$$;

CREATE TRIGGER configurations_set_condition_canonical_url_trigger
    BEFORE INSERT OR UPDATE OF condition_id ON configurations
    FOR EACH ROW EXECUTE FUNCTION configurations_set_condition_canonical_url_on_insert();

-- restore the version trigger and function
CREATE FUNCTION configurations_set_version_on_insert() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  max_version INTEGER;
BEGIN
  SELECT MAX(version)
  INTO max_version
  FROM configurations
  WHERE condition_canonical_url = NEW.condition_canonical_url
    AND jurisdiction_id = NEW.jurisdiction_id;

  IF max_version IS NULL THEN
    NEW.version := 1;
  ELSE
    NEW.version := max_version + 1;
  END IF;

  RETURN NEW;
END;
$$;

CREATE TRIGGER configurations_set_version_on_insert
    BEFORE INSERT ON configurations
    FOR EACH ROW EXECUTE FUNCTION configurations_set_version_on_insert();
