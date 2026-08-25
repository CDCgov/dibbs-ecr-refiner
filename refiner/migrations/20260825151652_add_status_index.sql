-- migrate:up
CREATE INDEX IF NOT EXISTS idx_configuration_status ON configurations (status);

-- migrate:down

DROP INDEX IF EXISTS idx_configuration_status;
