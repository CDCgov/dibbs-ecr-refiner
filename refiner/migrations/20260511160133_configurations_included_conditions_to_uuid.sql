-- migrate:up
ALTER TABLE configurations
    ALTER COLUMN included_conditions DROP DEFAULT;

ALTER TABLE configurations
    ALTER COLUMN included_conditions TYPE UUID[]
    USING translate(included_conditions::text, '[]', '{}')::UUID[];

ALTER TABLE configurations
    ALTER COLUMN included_conditions SET DEFAULT '{}'::UUID[];

-- migrate:down
ALTER TABLE configurations
    ALTER COLUMN included_conditions DROP DEFAULT;

ALTER TABLE configurations
    ALTER COLUMN included_conditions TYPE JSONB
    USING to_jsonb(included_conditions);

ALTER TABLE configurations
    ALTER COLUMN included_conditions SET DEFAULT '[]'::JSONB;
