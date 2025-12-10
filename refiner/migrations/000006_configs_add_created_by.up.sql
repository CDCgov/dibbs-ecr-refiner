-- add new column
ALTER TABLE configurations
ADD COLUMN created_by UUID NOT NULL;

-- add fk reference
ALTER TABLE configurations
ADD CONSTRAINT configurations_created_by_fkey
  FOREIGN KEY (created_by) REFERENCES users (id);
