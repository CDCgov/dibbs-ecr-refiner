-- migrate:up
CREATE TABLE systems (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
    key UNIQUE text NOT NULL,
    display_name UNIQUE text NOT NULL,
    oid text UNIQUE
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

);

-- migrate:down

DROP TABLE IF EXISTS systems;
