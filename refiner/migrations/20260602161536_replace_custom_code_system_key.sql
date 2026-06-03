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

ALTER TABLE events_custom_code_uploads RENAME COLUMN system TO system_key;

UPDATE events_custom_code_uploads
SET system_key = CASE system_key
    WHEN 'ICD-10' THEN 'icd10'
    WHEN 'SNOMED' THEN 'snomed'
    WHEN 'LOINC'  THEN 'loinc'
    WHEN 'RxNorm' THEN 'rxnorm'
    WHEN 'CVX'    THEN 'cvx'
    WHEN 'Other'  THEN 'other'
END
WHERE system_key IN ('ICD-10', 'SNOMED', 'LOINC', 'RxNorm', 'CVX', 'Other');



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

ALTER TABLE events_custom_code_uploads RENAME COLUMN system_key TO system;

UPDATE events_custom_code_uploads
SET system = CASE system
    WHEN 'icd10'  THEN 'ICD-10'
    WHEN 'snomed' THEN 'SNOMED'
    WHEN 'loinc'  THEN 'LOINC'
    WHEN 'rxnorm' THEN 'RxNorm'
    WHEN 'cvx'    THEN 'CVX'
    WHEN 'other'  THEN 'Other'
END
WHERE system IN ('icd10', 'snomed', 'loinc', 'rxnorm', 'cvx', 'other');