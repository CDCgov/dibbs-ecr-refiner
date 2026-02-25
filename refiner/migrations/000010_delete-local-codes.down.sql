ALTER TABLE configurations
    ADD COLUMN local_codes JSONB DEFAULT '{}'::jsonb;
