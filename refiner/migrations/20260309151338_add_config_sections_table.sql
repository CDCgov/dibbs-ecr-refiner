-- migrate:up
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'section_action') THEN
    CREATE TYPE section_action AS ENUM ('refine','retain');
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS configuration_sections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  configuration_id uuid NOT NULL REFERENCES configurations(id) ON DELETE CASCADE,

  code text NOT NULL,
  name text NOT NULL,
  action section_action NOT NULL,
  include boolean NOT NULL,
  narrative boolean NOT NULL,
  versions text[] NOT NULL DEFAULT '{}'::text[],

  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),

  UNIQUE (configuration_id, code)
);

CREATE INDEX IF NOT EXISTS configuration_sections_configuration_id_idx
  ON configuration_sections(configuration_id);

CREATE INDEX IF NOT EXISTS configuration_sections_code_idx
  ON configuration_sections(code);

-- backfill data
INSERT INTO configuration_sections (
  configuration_id, code, name, action, include, narrative, versions
)
SELECT
  c.id,
  e.val->>'code',
  e.val->>'name',
  (e.val->>'action')::section_action,
  (e.val->>'include')::boolean,
  (e.val->>'narrative')::boolean,
  ARRAY(SELECT jsonb_array_elements_text(e.val->'versions'))
FROM configurations c
CROSS JOIN LATERAL jsonb_array_elements(COALESCE(c.section_processing, '[]'::jsonb)) AS e(val)
ON CONFLICT (configuration_id, code)
DO UPDATE SET
  name       = EXCLUDED.name,
  action     = EXCLUDED.action,
  include    = EXCLUDED.include,
  narrative  = EXCLUDED.narrative,
  versions   = EXCLUDED.versions,
  updated_at = now();

-- drop old constraint and column
ALTER TABLE configurations
  DROP CONSTRAINT IF EXISTS section_processing_must_be_json_array;

ALTER TABLE configurations
  DROP COLUMN IF EXISTS section_processing;


-- migrate:down

ALTER TABLE configurations
  ADD COLUMN section_processing jsonb NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE configurations
  ADD CONSTRAINT section_processing_must_be_json_array
  CHECK (jsonb_typeof(section_processing) = 'array');

-- best effort reassemble
UPDATE configurations c
SET section_processing = COALESCE((
  SELECT jsonb_agg(
           jsonb_build_object(
             'code', s.code,
             'name', s.name,
             'action', s.action::text,
             'include', s.include,
             'versions', to_jsonb(s.versions),
             'narrative', s.narrative
           )
           ORDER BY s.code
         )
  FROM configuration_sections s
  WHERE s.configuration_id = c.id
), '[]'::jsonb);


DROP INDEX IF EXISTS configuration_sections_code_idx;
DROP INDEX IF EXISTS configuration_sections_configuration_id_idx;

DROP TABLE IF EXISTS configuration_sections;

DROP TYPE IF EXISTS section_action;
