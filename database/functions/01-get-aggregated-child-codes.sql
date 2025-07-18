-- =============================================================================
-- FUNCTION: get_aggregated_child_codes
--
-- this helper function takes a parent grouper's identity and a code column name
-- (e.g., 'loinc_codes') and returns a single JSONB array containing all unique
-- codes of that type from all of its linked children.
-- =============================================================================

CREATE OR REPLACE FUNCTION get_aggregated_child_codes(
    p_parent_url TEXT,
    p_parent_version TEXT,
    p_code_column_name TEXT
)
RETURNS JSONB AS $$
DECLARE
    aggregated_codes JSONB;
BEGIN
    EXECUTE format(
        $query$
        SELECT COALESCE(jsonb_agg(DISTINCT code), '[]'::jsonb)
        FROM (
            SELECT jsonb_array_elements_text(rsg.%1$I) as code
            FROM tes_reporting_spec_groupers rsg
            JOIN tes_condition_grouper_references ref
              ON rsg.canonical_url = ref.child_grouper_url
             AND rsg.version = ref.child_grouper_version
            WHERE ref.parent_grouper_url = %2$L
              AND ref.parent_grouper_version = %3$L
        ) as codes
        $query$,
        p_code_column_name,
        p_parent_url,
        p_parent_version
    ) INTO aggregated_codes;

    RETURN aggregated_codes;
END;
$$ LANGUAGE plpgsql;
