-- migrate:up
ALTER TABLE configurations
ADD COLUMN original_condition_id UUID REFERENCES conditions(id);

-- migrate:down
ALTER TABLE configurations
DROP COLUMN original_condition_id;
