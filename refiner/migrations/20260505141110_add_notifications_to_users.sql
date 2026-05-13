-- migrate:up

ALTER TABLE users
    ADD COLUMN notifications JSONB NOT NULL DEFAULT '{}'::jsonb;


-- migrate:down

ALTER TABLE users
DROP COLUMN notifications;