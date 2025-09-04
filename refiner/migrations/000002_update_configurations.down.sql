-- if we need to rollback the migration changes; run the following

-- restore original columns
ALTER TABLE configurations
    ADD COLUMN name TEXT,
    ADD COLUMN description TEXT,
    ADD COLUMN loinc_codes_additions JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN snomed_codes_additions JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN icd10_codes_additions JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN rxnorm_codes_additions JSONB DEFAULT '[]'::jsonb;

-- remove new columns
ALTER TABLE configurations
    DROP CONSTRAINT IF EXISTS fk_primary_condition,
    DROP COLUMN IF EXISTS condition_id,
    DROP COLUMN IF EXISTS local_codes;

-- restore original constraint
ALTER TABLE configurations
    ADD CONSTRAINT check_included_conditions
        CHECK (jsonb_array_length(included_conditions) > 0);
