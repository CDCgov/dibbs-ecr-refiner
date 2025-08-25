-- Drop triggers
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP TRIGGER IF EXISTS update_conditions_updated_at ON conditions;
DROP TRIGGER IF EXISTS update_configurations_updated_at ON configurations;
DROP TRIGGER IF EXISTS update_labels_updated_at ON labels;

-- Drop the trigger function
DROP FUNCTION IF EXISTS set_updated_at();

-- Drop join table
DROP TABLE IF EXISTS configuration_labels;

-- Drop indexes
DROP INDEX IF EXISTS idx_one_active_per_snomed;
DROP INDEX IF EXISTS idx_activations_active_lookup;
DROP INDEX IF EXISTS idx_conditions_child_snomed_codes;

-- Drop main tables
DROP TABLE IF EXISTS activations;
DROP TABLE IF EXISTS configurations;
DROP TABLE IF EXISTS labels;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS conditions;
DROP TABLE IF EXISTS jurisdictions;

-- Drop sequence
DROP SEQUENCE IF EXISTS configuration_family_id_seq;

-- Drop the older tables
DROP TABLE IF EXISTS filters;
DROP TABLE IF EXISTS groupers;
