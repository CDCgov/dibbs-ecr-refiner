-- migrate:up
ALTER TABLE conditions_codes RENAME CONSTRAINT conditions_rsg_codes_pkey
    TO conditions_codes_pkey;

-- migrate:down
ALTER TABLE conditions_codes RENAME CONSTRAINT conditions_codes_pkey
    TO conditions_rsg_codes_pkey;