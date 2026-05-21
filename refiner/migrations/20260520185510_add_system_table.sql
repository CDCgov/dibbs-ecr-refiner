-- migrate:up
CREATE TABLE systems (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
    key text UNIQUE NOT NULL,
    display_name text UNIQUE NOT NULL,
    oid text UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TRIGGER update_systems_updated_at
BEFORE UPDATE ON systems
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- migrate:down
DROP TRIGGER IF EXISTS update_systems_updated_at ON systems;

DROP TABLE IF EXISTS systems;
