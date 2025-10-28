CREATE type event_type_enum as ENUM (
    'create_configuration'
);

CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jurisdiction_id TEXT NOT NULL,
    user_id UUID,
    configuration_id UUID,
    event_type event_type_enum NOT NULL,
    action_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- null out user id if user record is deleted
    CONSTRAINT fk_user FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON DELETE SET NULL,

    -- null out config id if config record is deleted
    CONSTRAINT fk_configuration FOREIGN KEY (configuration_id)
        REFERENCES configurations (id)
        ON DELETE SET NULL
);
