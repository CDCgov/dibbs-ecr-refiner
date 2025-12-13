-- drop foreign key constraint
ALTER TABLE configurations
DROP CONSTRAINT IF EXISTS configurations_created_by_fkey;

-- drop the column
ALTER TABLE configurations
DROP COLUMN IF EXISTS created_by;
