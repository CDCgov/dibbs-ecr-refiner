-- migrate:up
CREATE TABLE IF NOT EXISTS events_custom_code_uploads (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id uuid NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    system text NOT NULL,
    code text NOT NULL,
    name text NOT NULL
)

-- migrate:down
DROP TABLE IF EXISTS events_custom_code_uploads;
