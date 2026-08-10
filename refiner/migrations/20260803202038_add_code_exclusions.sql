-- migrate:up

CREATE TABLE configurations_conditions_code_exclusions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    configuration_id UUID NOT NULL,
    condition_id UUID NOT NULL,
    code_id UUID NOT NULL REFERENCES codes(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- ON DELETE CASCADE is required: removing a condition from a configuration
    -- deletes the configurations_conditions row, and deleting a configuration
    -- cascades to it. Without this, either path raises a ForeignKeyViolation
    -- once the user has excluded any code from that condition.
    FOREIGN KEY (configuration_id, condition_id)
        REFERENCES configurations_conditions(configuration_id, condition_id)
        ON DELETE CASCADE,

    UNIQUE (configuration_id, condition_id, code_id)
);


-- migrate:down

DROP TABLE configurations_conditions_code_exclusions;
