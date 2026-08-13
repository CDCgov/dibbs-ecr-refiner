-- migrate:up
CREATE TABLE IF NOT EXISTS valuesets (
    id uuid DEFAULT  gen_random_uuid() PRIMARY KEY NOT NULL,
    external_id text NOT NULL,
    url text NOT NULL,
    parent_url text,
    name text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE conditions_codes
    ADD COLUMN valueset_id UUID,
    ADD CONSTRAINT fk_conditions_valuesets_fkey
    FOREIGN KEY (valueset_id) 
    REFERENCES valuesets (id)
    ON DELETE CASCADE;

-- migrate:down
ALTER TABLE conditions_codes
    DROP CONSTRAINT IF EXISTS fk_conditions_valuesets_fkey;

ALTER TABLE conditions_codes DROP COLUMN valueset_id;
DROP TABLE IF EXISTS valuesets;


