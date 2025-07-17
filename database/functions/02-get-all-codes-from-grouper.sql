-- =============================================================================
-- FUNCTION: get_all_codes_from_grouper
--
-- this helper function takes a single record from either the
-- `tes_condition_groupers` or `configurations` table and returns a single
-- JSONB array containing all of its codes (LOINC, SNOMED, etc.) flattened
-- into one list.
-- =============================================================================

CREATE OR REPLACE FUNCTION get_all_codes_from_grouper(
    p_grouper_record ANYELEMENT
)
RETURNS JSONB AS $$
BEGIN
    RETURN (
        COALESCE(p_grouper_record.loinc_codes, '[]'::jsonb) ||
        COALESCE(p_grouper_record.snomed_codes, '[]'::jsonb) ||
        COALESCE(p_grouper_record.icd10_codes, '[]'::jsonb) ||
        COALESCE(p_grouper_record.rxnorm_codes, '[]'::jsonb)
    );
END;
$$ LANGUAGE plpgsql;
