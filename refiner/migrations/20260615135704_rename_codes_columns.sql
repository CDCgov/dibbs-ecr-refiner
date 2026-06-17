-- migrate:up
ALTER TABLE codes
  RENAME COLUMN value TO code;

ALTER TABLE codes
  RENAME COLUMN name TO display;

ALTER TABLE custom_codes
  RENAME COLUMN value TO code;
  
ALTER TABLE custom_codes
  RENAME COLUMN name TO display;

-- migrate:down

ALTER TABLE codes
  RENAME COLUMN code TO value;

ALTER TABLE codes
  RENAME COLUMN display TO name;

ALTER TABLE custom_codes
  RENAME COLUMN code TO value;
  
ALTER TABLE custom_codes
  RENAME COLUMN display TO name;
