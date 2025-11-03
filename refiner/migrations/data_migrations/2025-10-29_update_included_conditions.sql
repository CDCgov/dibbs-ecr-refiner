UPDATE configurations c
SET included_conditions = (
    SELECT jsonb_agg(cond.id::text)
    FROM jsonb_array_elements(c.included_conditions) AS elem
             JOIN conditions cond
                  ON cond.canonical_url = elem->>'canonical_url'
    AND cond.version = elem->>'version'
    )
WHERE jsonb_typeof(c.included_conditions) = 'array'
  AND (c.included_conditions->0 ? 'canonical_url');