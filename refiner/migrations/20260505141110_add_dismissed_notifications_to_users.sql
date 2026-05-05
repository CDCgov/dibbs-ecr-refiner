-- migrate:up

ALTER TABLE users
    ADD COLUMN dismissed_notifications JSONB NOT NULL DEFAULT '{}'::jsonb;


-- migrate:down

ALTER TABLE users
DROP COLUMN dismissed_notifications;