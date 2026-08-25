-- migrate:up
ALTER TABLE configurations_conditions_code_exclusions 
DROP CONSTRAINT configurations_conditions_code_exclusions_configuration_id_fkey;

ALTER TABLE configurations_conditions_code_exclusions 
ADD CONSTRAINT configurations_conditions_code_exclusions_configuration_id_fkey 
FOREIGN KEY (configuration_id) 
REFERENCES configurations (id) 
ON DELETE CASCADE;

-- migrate:down

ALTER TABLE configurations_conditions_code_exclusions 
DROP CONSTRAINT configurations_conditions_code_exclusions_configuration_id_fkey;

ALTER TABLE configurations_conditions_code_exclusions 
ADD CONSTRAINT configurations_conditions_code_exclusions_configuration_id_fkey 
FOREIGN KEY (configuration_id) 
REFERENCES configurations (id);