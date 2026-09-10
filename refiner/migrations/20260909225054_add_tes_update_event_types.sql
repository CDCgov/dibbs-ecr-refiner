-- migrate:up

-- Add new TES update event types to the event_type_enum
ALTER TYPE event_type_enum ADD VALUE 'tes_update_existing_draft';
ALTER TYPE event_type_enum ADD VALUE 'tes_create_draft_from_active';

-- migrate:down

-- Note: PostgreSQL doesn't support removing enum values directly
-- A manual rollback would require recreating the enum without these values
-- This is intentionally left empty as enum value removal is complex
