-- migrate:up
ALTER TABLE events
ADD COLUMN condition_id UUID REFERENCES conditions(id),
ADD COLUMN code_count INTEGER;


-- migrate:down
ALTER TABLE events
DROP COLUMN code_count,
DROP COLUMN condition_id;
