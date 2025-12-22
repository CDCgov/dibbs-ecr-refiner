CREATE type event_type_enum as ENUM (
    'create_configuration',
    'activate_configuration',
    'deactivate_configuration',
    'add_code',
    'delete_code',
    'edit_code',
    'section_update'
);

CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jurisdiction_id TEXT NOT NULL,
    user_id UUID NOT NULL,
    configuration_id UUID NOT NULL,
    event_type event_type_enum NOT NULL,
    action_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_user FOREIGN KEY (user_id)
        REFERENCES users (id),

    CONSTRAINT fk_configuration FOREIGN KEY (configuration_id)
        REFERENCES configurations (id)
);
