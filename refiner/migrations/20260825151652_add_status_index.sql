-- migrate:up
CREATE INDEX CONCURRENTLY idx_configuration_status ON configurations (status);

-- migrate:down

DROP INDEX CONCURRENTLY IF EXISTS idx_configuration_status;
