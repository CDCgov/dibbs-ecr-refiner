-- migrate:up

CREATE TABLE IF NOT EXISTS valuesets (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    external_id text NOT NULL,
    url text NOT NULL,
    parent_url text,
    name text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);



-- migrate:down

