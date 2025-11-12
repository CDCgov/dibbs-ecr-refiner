-- triggers
DROP TRIGGER configurations_set_last_activated_at_on_status_change_trigger
ON configurations;

DROP TRIGGER configurations_set_version_on_insert_trigger
ON configurations;

DROP TRIGGER configurations_set_condition_canonical_url_trigger
ON configurations;

-- trigger functions
DROP FUNCTION configurations_set_last_activated_at_on_status_change();
DROP FUNCTION configurations_set_version_on_insert();
DROP FUNCTION configurations_set_condition_canonical_url_on_insert();

-- unique constraints
ALTER TABLE configurations
DROP CONSTRAINT configurations_unique_version_per_pair;

-- partial unique indexes
DROP INDEX configurations_one_active_per_pair_idx;
DROP INDEX configurations_one_draft_per_pair_idx;

-- added columns
ALTER TABLE configurations
DROP COLUMN status,
DROP COLUMN last_activated_at,
DROP COLUMN last_activated_by,
DROP COLUMN condition_canonical_url;

-- status enum
DROP TYPE configuration_status;
