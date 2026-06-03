-- migrate:up

-- Change "system" index to "system_key" and values to the new key values 

UPDATE configurations c 
SET custom_codes = COALESCE((
    SELECT jsonb_agg(
        (elem
        || CASE
                WHEN elem->>'system' = 'ICD-10' THEN '{"system_key": "icd10"}'::jsonb
                WHEN elem->>'system' = 'SNOMED' THEN '{"system_key": "snomed"}'::jsonb
                WHEN elem->>'system' = 'LOINC' THEN '{"system_key": "loinc"}'::jsonb
                WHEN elem->>'system' = 'RxNorm' THEN '{"system_key": "rxnorm"}'::jsonb
                WHEN elem->>'system' = 'CVX' THEN '{"system_key": "cvx"}'::jsonb
                WHEN elem->>'system' = 'Other' THEN '{"system_key": "other"}'::jsonb
                ELSE '{}'::jsonb
            END) - 'system'
            ORDER BY ord
    )
    FROM jsonb_array_elements(c.custom_codes) WITH ORDINALITY AS t(elem, ord)
), '[]'::jsonb) 
WHERE c.custom_codes IS NOT NULL
  AND jsonb_typeof(c.custom_codes) = 'array';


-- migrate:down
UPDATE configurations c 
SET custom_codes = COALESCE((
    SELECT jsonb_agg(
        (elem
        || CASE
                WHEN elem->>'system_key' = 'icd10' THEN '{"system": "ICD-10"}'::jsonb
                WHEN elem->>'system_key' = 'snomed' THEN '{"system":"SNOMED" }'::jsonb
                WHEN elem->>'system_key' = 'loinc' THEN '{"system":"LOINC" }'::jsonb
                WHEN elem->>'system_key' = 'rxnorm' THEN '{"system":"RxNorm" }'::jsonb
                WHEN elem->>'system_key' = 'cvx' THEN '{"system":"CVX" }'::jsonb
                WHEN elem->>'system_key' = 'other' THEN '{"system":"Other" }'::jsonb
                ELSE '{}'::jsonb
            END) - 'system_key'
            ORDER BY ord
    )
    FROM jsonb_array_elements(c.custom_codes) WITH ORDINALITY AS t(elem, ord)
), '[]'::jsonb) 
WHERE c.custom_codes IS NOT NULL
  AND jsonb_typeof(c.custom_codes) = 'array';
