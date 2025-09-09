-- add new columns
-- **condition_id**
-- initially we planned to use the `activations` table to track the explicit relationships between
-- the RC SNOMED codes, RSG codes, and their parent CG. instead, we'll ensure that all configurations
-- are _explicitly_ tied to a condition. this will ensure that we know immediately which condition any
-- configuration is set up for and allow for `included_conditions` to simply track both the primary
-- condition and its secondary conditions
-- **local_codes**
-- initially we planned to store the snomed, loinc, icd10, and rxnorm codes in:
-- - loinc_codes_additions, snomed_codes_additions, icd10_codes_additions, and rxnorm_codes_additions
-- instead we'll store the data as a FHIR Coding (code, display, system) in `custom_codes`
-- in anticipation of needing the same functionality but for nonstandard code systems and local codes,
-- we're adding `local_codes` and let it function in a similar way to `custom_codes`
ALTER TABLE configurations
    ADD COLUMN condition_id UUID NOT NULL REFERENCES conditions(id),
    ADD COLUMN local_codes JSONB DEFAULT '{}'::jsonb;

-- drop unnecessary columns
-- since we're not using these to store user driven "custom codes" there's
-- no reason to keep them around
ALTER TABLE configurations
    DROP COLUMN description,
    DROP COLUMN loinc_codes_additions,
    DROP COLUMN snomed_codes_additions,
    DROP COLUMN icd10_codes_additions,
    DROP COLUMN rxnorm_codes_additions;

-- update constraints
-- * previously, the configurations table used a constraint named configurations_must_have_conditions
-- to ensure at least one condition was included (jsonb_array_length(included_conditions) > 0)
-- * this migration removes that constraint in favor of requiring an explicit condition_id foreign key
-- which more directly and reliably ties every configuration to a condition.
ALTER TABLE configurations
    DROP CONSTRAINT configurations_must_have_conditions;
