-- migrate:up
-- add column for CVX codes which correspond to immunization related codes
ALTER TABLE conditions ADD COLUMN cvx_codes jsonb;


-- migrate:down
ALTER TABLE conditions DROP COLUMN cvx_codes;


