-- migrate:up
ALTER TABLE configurations
  RENAME COLUMN s3_urls TO s3_url;

ALTER TABLE configurations
  ALTER COLUMN s3_url TYPE TEXT USING s3_url[1];

-- migrate:down
ALTER TABLE configurations
  ALTER COLUMN s3_url TYPE TEXT[] USING NULLIF(ARRAY[s3_url], ARRAY[NULL::TEXT]);

ALTER TABLE configurations
  RENAME COLUMN s3_url TO s3_urls;
