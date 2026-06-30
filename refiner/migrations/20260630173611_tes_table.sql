-- migrate:up

-- create the tes table
CREATE TABLE tes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- populate tes with the distinct versions from conditions
INSERT INTO tes (version)
SELECT DISTINCT version FROM conditions;

-- add tes_id foreign key to conditions
ALTER TABLE conditions
    ADD COLUMN tes_id UUID REFERENCES tes(id);

-- link each condition to its corresponding tes row
UPDATE conditions c
SET tes_id = t.id
FROM tes t
WHERE t.version = c.version;

-- make tes_id NOT NULL now that all rows are populated
ALTER TABLE conditions
    ALTER COLUMN tes_id SET NOT NULL;

-- migrate:down

ALTER TABLE conditions DROP COLUMN tes_id;
DROP TABLE tes;
