-- migrate:up
-- Add the 'keep_on_match' value to the section_narrative enum so that
-- the refiner can persist the new "Keep on match" narrative option.
ALTER TYPE section_narrative ADD VALUE IF NOT EXISTS 'keep_on_match';


-- migrate:down
-- PostgreSQL does not support removing values from an enum type, so the
-- down migration rebuilds the enum without 'keep_on_match'. Any rows
-- currently set to 'keep_on_match' are coerced to 'retain' to avoid
-- losing data.
ALTER TYPE section_narrative RENAME TO section_narrative_old;

CREATE TYPE section_narrative AS ENUM ('retain', 'remove', 'reconstruct');

ALTER TABLE configurations_sections
  ALTER COLUMN narrative DROP DEFAULT,
  ALTER COLUMN narrative TYPE section_narrative
    USING (
      CASE
        WHEN narrative::text = 'keep_on_match' THEN 'retain'::section_narrative
        ELSE narrative::text::section_narrative
      END
    );

DROP TYPE section_narrative_old;
