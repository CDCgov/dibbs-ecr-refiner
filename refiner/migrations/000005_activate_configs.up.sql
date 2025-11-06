-- valid status types
CREATE TYPE configuration_status AS ENUM ('active', 'inactive', 'draft');

-- update table with new columns
ALTER TABLE configurations
ADD COLUMN status configuration_status DEFAULT 'draft',
ADD COLUMN last_activated_at TIMESTAMPTZ,
ADD COLUMN last_activated_by UUID,
ADD COLUMN condition_canonical_url TEXT;

-- add fk reference
ALTER TABLE configurations
ADD CONSTRAINT configurations_last_activated_by_fkey
  FOREIGN KEY (last_activated_by) REFERENCES users (id);

-- update existing rows with canonical url
UPDATE configurations c
SET condition_canonical_url = cond.canonical_url
FROM conditions cond
WHERE c.condition_id = cond.id;

-- every row must now have a canonical url
ALTER TABLE configurations
ALTER COLUMN condition_canonical_url SET NOT NULL;

-- update existing rows to have 'draft' as the status
UPDATE configurations SET status = 'draft' WHERE status IS NULL;

-- every row must now be a 'draft'
ALTER TABLE configurations
ALTER COLUMN status SET NOT NULL;

-- enforce one active config at a time
CREATE UNIQUE INDEX configurations_one_active_per_pair_idx
  ON configurations (condition_canonical_url, jurisdiction_id)
  WHERE status = 'active';

-- enforce one draft config at a time
CREATE UNIQUE INDEX configurations_one_draft_per_pair_idx
  ON configurations (condition_canonical_url, jurisdiction_id)
  WHERE status = 'draft';

-- auto update last_activated_at
CREATE FUNCTION configurations_set_last_activated_at_on_status_change()
RETURNS TRIGGER AS $$
BEGIN
  -- when going from any status to "active" we update `last_activated_at`
  IF NEW.status = 'active' AND OLD.status IS DISTINCT FROM 'active' THEN
    NEW.last_activated_at := NOW();
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- trigger for function above
CREATE TRIGGER configurations_set_last_activated_at_on_status_change_trigger
BEFORE UPDATE OF status ON configurations
FOR EACH ROW
EXECUTE FUNCTION configurations_set_last_activated_at_on_status_change();

-- set version number on insert
CREATE FUNCTION configurations_set_version_on_insert()
RETURNS TRIGGER AS $$
DECLARE
  max_version INTEGER;
BEGIN
  -- find the highest version for the condition/jurisdiction pair
  SELECT MAX(version)
  INTO max_version
  FROM configurations
  WHERE condition_canonical_url = NEW.condition_canonical_url
    AND jurisdiction_id = NEW.jurisdiction_id;

  -- if none exist yet, start at 1 otherwise increment previous max
  IF max_version IS NULL THEN
    NEW.version := 1;
  ELSE
    NEW.version := max_version + 1;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- trigger for function above
CREATE TRIGGER configurations_set_version_on_insert_trigger
BEFORE INSERT ON configurations
FOR EACH ROW
EXECUTE FUNCTION configurations_set_version_on_insert();

-- enforce unique versioning
ALTER TABLE configurations
ADD CONSTRAINT configurations_unique_version_per_pair
  UNIQUE (condition_canonical_url, jurisdiction_id, version);

-- auto set canonical url on insert
CREATE FUNCTION configurations_set_condition_canonical_url_on_insert()
RETURNS TRIGGER AS $$
BEGIN
  -- grab canonical_url from conditions when inserting or updating condition_id
  SELECT canonical_url
  INTO NEW.condition_canonical_url
  FROM conditions
  WHERE id = NEW.condition_id
  LIMIT 1;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- trigger for function above
CREATE TRIGGER configurations_set_condition_canonical_url_trigger
BEFORE INSERT OR UPDATE OF condition_id ON configurations
FOR EACH ROW
EXECUTE FUNCTION configurations_set_condition_canonical_url_on_insert();
