-- migrate:up
CREATE TABLE systems (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
    key text UNIQUE NOT NULL,
    display_name text UNIQUE NOT NULL,
    oid text UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- migrate:down

DROP TABLE IF EXISTS systems;
