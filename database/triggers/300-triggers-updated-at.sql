-- Automatically update updated_at timestamp on record modification
-- These triggers ensure data consistency without application-level code

CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER update_conditions_updated_at
BEFORE UPDATE ON conditions
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER update_configurations_updated_at
BEFORE UPDATE ON configurations
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER update_labels_updated_at
BEFORE UPDATE ON labels
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
