-- migrate:up
ALTER TABLE conditions DROP COLUMN version;

-- add unique constraint for canonical_url/tes_id pair
ALTER TABLE conditions
ADD CONSTRAINT conditions_canonical_url_tes_id_key
UNIQUE (canonical_url, tes_id);

-- migrate:down

ALTER TABLE conditions
DROP CONSTRAINT conditions_canonical_url_tes_id_key;

ALTER TABLE conditions ADD COLUMN version TEXT;

UPDATE conditions c
SET version = t.version
FROM tes t
WHERE t.id = c.tes_id;

ALTER TABLE conditions ALTER COLUMN version SET NOT NULL;
