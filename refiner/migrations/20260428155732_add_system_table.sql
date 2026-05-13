-- migrate:up
CREATE TABLE systems (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    display_name text NOT NULL,
    oid text NOT NULL UNIQUE
);

-- migrate:down

DROP TABLE IF EXISTS systems;
