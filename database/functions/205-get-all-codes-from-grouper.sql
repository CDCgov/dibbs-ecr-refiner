-- =============================================================================
-- FUNCTION: get_all_codes_from_grouper
--
-- this helper function takes a single record and returns a single TEXT ARRAY
-- containing all of its codes, extracting them from the various JSONB columns.
-- This version robustly checks that a code column both exists and contains
-- a JSON array before attempting to extract elements from it
-- =============================================================================

CREATE OR REPLACE FUNCTION get_all_codes_from_grouper(
    p_grouper_record ANYELEMENT
)
RETURNS TEXT[] AS $$
DECLARE
    rec_jsonb JSONB := to_jsonb(p_grouper_record);
    codes_array TEXT[] := ARRAY[]::TEXT[];
BEGIN
    -- only process if the key's value is a JSON array
    IF jsonb_typeof(rec_jsonb->'loinc_codes') = 'array' THEN
        codes_array := codes_array || ARRAY(SELECT jsonb_array_elements_text(rec_jsonb->'loinc_codes'));
    END IF;
    IF jsonb_typeof(rec_jsonb->'snomed_codes') = 'array' THEN
        codes_array := codes_array || ARRAY(SELECT jsonb_array_elements_text(rec_jsonb->'snomed_codes'));
    END IF;
    IF jsonb_typeof(rec_jsonb->'icd10_codes') = 'array' THEN
        codes_array := codes_array || ARRAY(SELECT jsonb_array_elements_text(rec_jsonb->'icd10_codes'));
    END IF;
    IF jsonb_typeof(rec_jsonb->'rxnorm_codes') = 'array' THEN
        codes_array := codes_array || ARRAY(SELECT jsonb_array_elements_text(rec_jsonb->'rxnorm_codes'));
    END IF;

    RETURN codes_array;
END;
$$ LANGUAGE plpgsql;
