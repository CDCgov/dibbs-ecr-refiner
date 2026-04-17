-- migrate:up
ALTER TYPE event_type_enum
    ADD VALUE IF NOT EXISTS 'bulk_add_custom_code';

-- migrate:down
-- irreversible: enum values cannot be removed safely
SELECT 1;
