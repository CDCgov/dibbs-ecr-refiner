-- triggers
DROP TRIGGER IF EXISTS configurations_set_last_activated_at_on_status_change_trigger
ON configurations;

DROP TRIGGER IF EXISTS configurations_set_version_on_insert_trigger
ON configurations;

-- trigger functions
DROP FUNCTION IF EXISTS configurations_set_last_activated_at_on_status_change();
DROP FUNCTION IF EXISTS configurations_set_version_on_insert();

-- unique constraints
ALTER TABLE configurations
DROP CONSTRAINT IF EXISTS configurations_unique_version_per_pair;

-- partial unique indexes
DROP INDEX IF EXISTS configurations_one_active_per_pair_idx;
DROP INDEX IF EXISTS configurations_one_draft_per_pair_idx;

-- added columns
ALTER TABLE configurations
DROP COLUMN IF EXISTS status,
DROP COLUMN IF EXISTS last_activated_at,
DROP COLUMN IF EXISTS activated_by,
DROP COLUMN IF EXISTS s3_url;

-- status enum
DROP TYPE IF EXISTS configuration_status;
