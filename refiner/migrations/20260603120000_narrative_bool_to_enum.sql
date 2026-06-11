-- migrate:up
-- Create the new enum type for narrative
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'section_narrative') THEN
    CREATE TYPE section_narrative AS ENUM ('retain', 'remove', 'reconstruct');
  END IF;
END $$;

-- Add new column with enum type
ALTER TABLE configurations_sections
  ADD COLUMN narrative_new section_narrative;

-- Migrate data: true -> 'retain', false -> 'remove'
UPDATE configurations_sections
SET narrative_new = CASE
  WHEN narrative = true THEN 'retain'::section_narrative
  WHEN narrative = false THEN 'remove'::section_narrative
END;

-- Make the new column NOT NULL
ALTER TABLE configurations_sections
  ALTER COLUMN narrative_new SET NOT NULL;

-- Drop the old boolean column
ALTER TABLE configurations_sections
  DROP COLUMN narrative;

-- Rename the new column to 'narrative'
ALTER TABLE configurations_sections
  RENAME COLUMN narrative_new TO narrative;


-- migrate:down
-- Add back the boolean column
ALTER TABLE configurations_sections
  ADD COLUMN narrative_old boolean;

-- Migrate data back: 'retain' -> true, 'remove'/'reconstruct' -> false
UPDATE configurations_sections
SET narrative_old = CASE
  WHEN narrative = 'retain' THEN true
  ELSE false
END;

-- Make the old column NOT NULL
ALTER TABLE configurations_sections
  ALTER COLUMN narrative_old SET NOT NULL;

-- Drop the enum column
ALTER TABLE configurations_sections
  DROP COLUMN narrative;

-- Rename back to 'narrative'
ALTER TABLE configurations_sections
  RENAME COLUMN narrative_old TO narrative;

-- Drop the enum type
DROP TYPE IF EXISTS section_narrative;
