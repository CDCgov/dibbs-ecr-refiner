-- migrate:up
CREATE TABLE custom_codes(
    id uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
    name TEXT NOT NULL,
    value TEXT NOT NULL,
    system_id UUID NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT custom_codes_system_id_fkey 
            FOREIGN KEY (system_id) 
            REFERENCES systems (id) 
            ON DELETE CASCADE
);

CREATE TABLE codes(
    id uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
    name TEXT NOT NULL,
    value TEXT NOT NULL,
    system_id UUID NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fk_codes_system_id_fkey 
        FOREIGN KEY (system_id) 
        REFERENCES systems (id) 
        ON DELETE CASCADE
);

CREATE TRIGGER update_custom_codes_updated_at
BEFORE UPDATE ON custom_codes
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


CREATE TRIGGER update_codes_updated_at
BEFORE UPDATE ON codes
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


-- migrate:down
DROP TABLE custom_codes;
DROP TABLE codes;