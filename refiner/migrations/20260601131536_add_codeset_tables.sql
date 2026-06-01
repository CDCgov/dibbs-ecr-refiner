-- migrate:up
CREATE TABLE custom_codes(
    id uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
    display_name TEXT NOT NULL,
    code TEXT NOT NULL
    system_id UUID NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (system_id) REFERENCES systems(id)

)

CREATE TABLE codes(
    id uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
    display_name TEXT NOT NULL,
    code TEXT NOT NULL
    system_id UUID NOT NULL REFERENCES systems(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (system_id) REFERENCES systems(id)
)

CREATE TRIGGER update_custom_codes_updated_at
BEFORE UPDATE ON custom_codes
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


CREATE TRIGGER update_codes_updated_at
BEFORE UPDATE ON codes
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- migrate:down
DROP TRIGGER IF EXISTS update_custom_codes_updated_at ON custom_codes;
DROP TRIGGER IF EXISTS update_codes_updated_at ON codes;

DROP TABLE custom_codes;
DROP TABLE codes;