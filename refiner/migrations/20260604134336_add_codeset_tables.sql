-- migrate:up
CREATE TABLE IF NOT EXISTS custom_codes(
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    value TEXT NOT NULL,
    system_id UUID NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (system_id, value),
    CONSTRAINT custom_codes_system_id_fkey 
            FOREIGN KEY (system_id) 
            REFERENCES systems (id) 
            ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS codes(
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    value TEXT NOT NULL,
    version TEXT NOT NULL,
    system_id UUID NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),    
    UNIQUE (system_id, version, value),
    CONSTRAINT fk_codes_system_id_fkey 
        FOREIGN KEY (system_id) 
        REFERENCES systems (id) 
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS condition_child_rsg_codes (
    code_id UUID REFERENCES codes(id) ON DELETE CASCADE, 
    condition_id UUID REFERENCES conditions(id) ON DELETE CASCADE,
    PRIMARY KEY (condition_id, code_id)
);

ALTER TABLE conditions_context_groupers 
    DROP CONSTRAINT conditions_context_groupers_condition_id_fkey;

ALTER TABLE conditions_context_groupers 
    ADD CONSTRAINT conditions_context_groupers_condition_id_fkey 
    FOREIGN KEY (condition_id) 
    REFERENCES conditions (id) 
    ON UPDATE CASCADE 
    ON DELETE CASCADE;

ALTER TABLE configurations_conditions 
    DROP CONSTRAINT configurations_conditions_condition_id_fkey;

ALTER TABLE configurations_conditions 
    ADD CONSTRAINT configurations_conditions_condition_id_fkey 
    FOREIGN KEY (condition_id) 
    REFERENCES conditions (id) 
    ON UPDATE CASCADE 
    ON DELETE CASCADE;

CREATE TRIGGER update_custom_codes_updated_at
BEFORE UPDATE ON custom_codes
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


CREATE TRIGGER update_codes_updated_at
BEFORE UPDATE ON codes
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


-- migrate:down
ALTER TABLE conditions_context_groupers 
    DROP CONSTRAINT conditions_context_groupers_condition_id_fkey;

ALTER TABLE conditions_context_groupers 
    ADD CONSTRAINT conditions_context_groupers_condition_id_fkey 
    FOREIGN KEY (condition_id) 
    REFERENCES conditions (id) 
    ON DELETE CASCADE;


ALTER TABLE configurations_conditions 
    DROP CONSTRAINT configurations_conditions_condition_id_fkey;

ALTER TABLE configurations_conditions 
    ADD CONSTRAINT configurations_conditions_condition_id_fkey 
    FOREIGN KEY (condition_id) 
    REFERENCES conditions (id) 
    ON DELETE CASCADE;

DROP TABLE IF EXISTS condition_child_rsg_codes;
DROP TABLE IF EXISTS custom_codes;
DROP TABLE IF EXISTS codes;