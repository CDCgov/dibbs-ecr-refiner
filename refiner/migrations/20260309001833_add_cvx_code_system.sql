-- migrate:up
-- add column for CVX codes which correspond to immunization related codes
ALTER TABLE conditions ADD COLUMN cvx_codes jsonb;
-- add column for packaging the output on s3
ALTER TABLE conditions ADD COLUMN output_name text;


-- migrate:down
ALTER TABLE conditions DROP COLUMN cvx_codes;
ALTER TABLE conditions DROP COLUMN output_name text;


