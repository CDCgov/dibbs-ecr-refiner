-- migrate:up

-- Add missing keys to sections
-- Change "remove" action to "refine" since it no longer exists
UPDATE configurations c
SET section_processing = COALESCE((
  SELECT jsonb_agg(
           (
             elem
             || '{"include": true, "narrative": false}'::jsonb
             || CASE
                  WHEN elem->>'action' = 'remove'
                    THEN '{"action": "refine"}'::jsonb
                  ELSE '{}'::jsonb
                END
           )
           ORDER BY ord
         )
  FROM jsonb_array_elements(c.section_processing) WITH ORDINALITY AS t(elem, ord)
), '[]'::jsonb)
WHERE c.section_processing IS NOT NULL
  AND jsonb_typeof(c.section_processing) = 'array';

-- migrate:down

-- Delete "include" and "narrative", leave "action" alone
UPDATE configurations c
SET section_processing = COALESCE((
  SELECT jsonb_agg(
           (elem - 'include' - 'narrative')
           ORDER BY ord
         )
  FROM jsonb_array_elements(c.section_processing) WITH ORDINALITY AS t(elem, ord)
), '[]'::jsonb)
WHERE c.section_processing IS NOT NULL
  AND jsonb_typeof(c.section_processing) = 'array';
