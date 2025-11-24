CREATE TABLE configuration_locks (
    configuration_id UUID PRIMARY KEY REFERENCES configurations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_configuration_locks_expires_at ON configuration_locks(expires_at);
