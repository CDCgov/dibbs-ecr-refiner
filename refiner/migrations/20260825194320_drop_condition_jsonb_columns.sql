-- migrate:up
ALTER TABLE configurations_conditions_code_exclusions
DROP CONSTRAINT configurations_conditions_code_exclusions_configuration_id_fkey;

ALTER TABLE configurations_conditions_code_exclusions
ADD CONSTRAINT configurations_conditions_code_exclusions_configuration_id_fkey
FOREIGN KEY (configuration_id)
REFERENCES configurations (id)
ON DELETE CASCADE;

ALTER TABLE conditions
    DROP COLUMN snomed_codes,
    DROP COLUMN loinc_codes,
    DROP COLUMN icd10_codes,
    DROP COLUMN rxnorm_codes,
    DROP COLUMN cvx_codes;

-- migrate:down

ALTER TABLE configurations_conditions_code_exclusions
DROP CONSTRAINT configurations_conditions_code_exclusions_configuration_id_fkey;

ALTER TABLE configurations_conditions_code_exclusions
ADD CONSTRAINT configurations_conditions_code_exclusions_configuration_id_fkey
FOREIGN KEY (configuration_id)
REFERENCES configurations (id);


-- Re-add codes columns
ALTER TABLE conditions
    ADD COLUMN snomed_codes jsonb,
    ADD COLUMN loinc_codes jsonb,
    ADD COLUMN icd10_codes jsonb,
    ADD COLUMN rxnorm_codes jsonb,
    ADD COLUMN cvx_codes jsonb;

WITH codes_to_add AS (
    SELECT 
        crc.condition_id,
        JSONB_AGG(
            JSONB_BUILD_OBJECT('code', c.code, 'display', c.display)
        ) FILTER (WHERE s.key = 'loinc') AS loinc_codes,
        JSONB_AGG(
            JSONB_BUILD_OBJECT('code', c.code, 'display', c.display)
        ) FILTER (WHERE s.key = 'snomed') AS snomed_codes,
        JSONB_AGG(
            JSONB_BUILD_OBJECT('code', c.code, 'display', c.display)
        ) FILTER (WHERE s.key = 'cvx') AS cvx_codes,
        JSONB_AGG(
            JSONB_BUILD_OBJECT('code', c.code, 'display', c.display)
        ) FILTER (WHERE s.key = 'icd10') AS icd10_codes,
        JSONB_AGG(
            JSONB_BUILD_OBJECT('code', c.code, 'display', c.display)
        ) FILTER (WHERE s.key = 'rxnorm') AS rxnorm_codes

    FROM conditions cond
    JOIN conditions_codes_temp crc ON crc.condition_id = cond.id
    JOIN codes c ON c.id = crc.code_id
    JOIN systems s ON s.id = c.system_id
    GROUP BY crc.condition_id
)
UPDATE conditions cond
SET 
    loinc_codes = COALESCE(cta.loinc_codes, '[]'::jsonb),
    snomed_codes = COALESCE(cta.snomed_codes, '[]'::jsonb),
    cvx_codes = COALESCE(cta.cvx_codes, '[]'::jsonb),
    icd10_codes = COALESCE(cta.icd10_codes, '[]'::jsonb),
    rxnorm_codes = COALESCE(cta.rxnorm_codes, '[]'::jsonb)
FROM codes_to_add cta
WHERE cond.id = cta.condition_id;