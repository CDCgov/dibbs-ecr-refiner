-- migrate:up
ALTER TYPE event_type_enum
    ADD VALUE IF NOT EXISTS 'bulk_delete_custom_code';

ALTER TABLE events_custom_code_uploads RENAME TO events_custom_codes;


-- migrate:down

ALTER TABLE events_custom_codes RENAME TO events_custom_code_uploads;
