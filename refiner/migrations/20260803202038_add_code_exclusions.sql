-- migrate:up

CREATE TABLE configurations_conditions_code_exclusions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    configuration_id UUID NOT NULL,
    condition_id UUID NOT NULL,
    code_id UUID NOT NULL REFERENCES codes(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    FOREIGN KEY (configuration_id, condition_id)
        REFERENCES configurations_conditions(configuration_id, condition_id),

    UNIQUE (configuration_id, condition_id, code_id)
);


-- migrate:down

DROP TABLE configurations_conditions_code_exclusions;
