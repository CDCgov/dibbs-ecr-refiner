-- migrate:up
-- Normalize stale (action, narrative) combinations on existing
-- configurations_sections rows. The application enforces these rules
-- going forward via the API validators in
-- `app/api/v1/configurations/sections.py` and the clone path in
-- `app/services/configurations.py`. This one-shot backfill brings
-- existing rows in line with the same rules so the database
-- representation matches what the API will now accept.
--
-- The single source of truth for these rules is
-- `app/services/ecr/policy.py::normalize_section_narrative`. Keep this
-- migration in sync with that function if rules are added or relaxed.
--
-- Rules applied (in order, idempotent):
--   1. Narrative-only sections must have action='retain'.
--      Codes: 10154-3, 29299-5, 10164-2, 10187-3.
--   2. Disabled (system-skipped) sections must have action='retain'.
--      Codes: 83910-0, 88085-6.
--   3. narrative in ('reconstruct', 'keep_on_match') requires
--      action='refine'; otherwise coerce narrative to 'retain'.
--   4. narrative='reconstruct' is only valid on
--      ReconstructableSection codes. Currently only 30954-2. Otherwise
--      coerce narrative to 'retain'.

-- rule 1
UPDATE configurations_sections
SET action = 'retain'
WHERE code IN ('10154-3', '29299-5', '10164-2', '10187-3')
  AND action <> 'retain';

-- rule 2
UPDATE configurations_sections
SET action = 'retain'
WHERE code IN ('83910-0', '88085-6')
  AND action <> 'retain';

-- rule 3 (run after rules 1-2 so we see the coerced action)
UPDATE configurations_sections
SET narrative = 'retain'
WHERE narrative IN ('reconstruct', 'keep_on_match')
  AND action <> 'refine';

-- rule 4
UPDATE configurations_sections
SET narrative = 'retain'
WHERE narrative = 'reconstruct'
  AND code <> '30954-2';


-- migrate:down
-- One-shot data backfill — no inverse. The original `narrative` /
-- `action` values were not preserved, and the previous state was, by
-- definition, invalid. Leaving as no-op is the only sane down path.
SELECT 1;
