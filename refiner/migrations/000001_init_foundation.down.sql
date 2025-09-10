-- Drop triggers
DROP TRIGGER update_users_updated_at ON users;
DROP TRIGGER update_conditions_updated_at ON conditions;
DROP TRIGGER update_configurations_updated_at ON configurations;
DROP TRIGGER update_labels_updated_at ON labels;

-- Drop the trigger function
DROP FUNCTION set_updated_at();

-- Drop join table
DROP TABLE configuration_labels;

-- Drop indexes
DROP INDEX idx_one_active_per_snomed;
DROP INDEX idx_activations_active_lookup;
DROP INDEX idx_conditions_child_snomed_codes;

-- Drop main tables
DROP TABLE activations;
DROP TABLE configurations;
DROP TABLE labels;
DROP TABLE sessions;
DROP TABLE users;
DROP TABLE conditions;
DROP TABLE jurisdictions;

-- Drop sequence
DROP SEQUENCE configuration_family_id_seq;

-- Drop the older tables
DROP TABLE filters;
DROP TABLE groupers;
