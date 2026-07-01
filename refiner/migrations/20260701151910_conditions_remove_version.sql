-- migrate:up
ALTER TABLE conditions DROP COLUMN version;

-- migrate:down
ALTER TABLE conditions ADD COLUMN version TEXT;

UPDATE conditions c
SET version = t.version
FROM tes t
WHERE t.id = c.tes_id;

ALTER TABLE conditions ALTER COLUMN version SET NOT NULL;
