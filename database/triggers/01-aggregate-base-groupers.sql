-- =============================================================================
-- TRIGGER 1: aggregation--when child `tes_reporting_spec_groupers`
-- are linked to a parent `tes_condition_grouper`, a trigger fires
-- to aggregate all unique codes (LOINC, SNOMED, ICD-10, RxNorm)
-- from the children into the parent's `jsonb` columns
-- =============================================================================

CREATE OR REPLACE FUNCTION update_parent_on_child_change()
RETURNS TRIGGER AS $$
DECLARE
    parent_url_to_update VARCHAR;
    parent_version_to_update VARCHAR;
BEGIN
    -- CASE 1: a reference was added, changed, or removed
    -- we need to find the parent from the OLD or NEW reference row
    IF (TG_TABLE_NAME = 'tes_condition_grouper_references') THEN
        IF (TG_OP = 'DELETE') THEN
            parent_url_to_update := OLD.parent_grouper_url;
            parent_version_to_update := OLD.parent_grouper_version;
        ELSE
            parent_url_to_update := NEW.parent_grouper_url;
            parent_version_to_update := NEW.parent_grouper_version;
        END IF;

    -- CASE 2: a child RS grouper's codes were updated directly
    -- we need to find the parent by looking up the reference
    ELSIF (TG_TABLE_NAME = 'tes_reporting_spec_groupers' AND TG_OP = 'UPDATE') THEN
        SELECT parent_grouper_url, parent_grouper_version
        INTO parent_url_to_update, parent_version_to_update
        FROM tes_condition_grouper_references
        WHERE child_grouper_url = NEW.canonical_url AND child_grouper_version = NEW.version
        LIMIT 1;
    END IF;

    -- if we have a parent to update, perform the aggregation
    IF parent_url_to_update IS NOT NULL THEN
        UPDATE tes_condition_groupers
        SET
            loinc_codes = COALESCE((
                SELECT jsonb_agg(DISTINCT code)
                FROM (
                    SELECT jsonb_array_elements_text(rsg.loinc_codes) as code
                    FROM tes_reporting_spec_groupers rsg
                    JOIN tes_condition_grouper_references ref ON rsg.canonical_url = ref.child_grouper_url AND rsg.version = ref.child_grouper_version
                    WHERE ref.parent_grouper_url = parent_url_to_update AND ref.parent_grouper_version = parent_version_to_update
                ) as codes
            ), '[]'::jsonb),
            snomed_codes = COALESCE((
                SELECT jsonb_agg(DISTINCT code)
                FROM (
                    SELECT jsonb_array_elements_text(rsg.snomed_codes) as code
                    FROM tes_reporting_spec_groupers rsg
                    JOIN tes_condition_grouper_references ref ON rsg.canonical_url = ref.child_grouper_url AND rsg.version = ref.child_grouper_version
                    WHERE ref.parent_grouper_url = parent_url_to_update AND ref.parent_grouper_version = parent_version_to_update
                ) as codes
            ), '[]'::jsonb),
            icd10_codes = COALESCE((
                SELECT jsonb_agg(DISTINCT code)
                FROM (
                    SELECT jsonb_array_elements_text(rsg.icd10_codes) as code
                    FROM tes_reporting_spec_groupers rsg
                    JOIN tes_condition_grouper_references ref ON rsg.canonical_url = ref.child_grouper_url AND rsg.version = ref.child_grouper_version
                    WHERE ref.parent_grouper_url = parent_url_to_update AND ref.parent_grouper_version = parent_version_to_update
                ) as codes
            ), '[]'::jsonb),
            rxnorm_codes = COALESCE((
                SELECT jsonb_agg(DISTINCT code)
                FROM (
                    SELECT jsonb_array_elements_text(rsg.rxnorm_codes) as code
                    FROM tes_reporting_spec_groupers rsg
                    JOIN tes_condition_grouper_references ref ON rsg.canonical_url = ref.child_grouper_url AND rsg.version = ref.child_grouper_version
                    WHERE ref.parent_grouper_url = parent_url_to_update AND ref.parent_grouper_version = parent_version_to_update
                ) as codes
            ), '[]'::jsonb)
        WHERE canonical_url = parent_url_to_update AND version = parent_version_to_update;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- create a trigger that fires when the relationship between groupers changes
CREATE TRIGGER trigger_update_parent_on_ref_change
AFTER INSERT OR UPDATE OR DELETE ON tes_condition_grouper_references
FOR EACH ROW EXECUTE FUNCTION update_parent_on_child_change();

-- create a trigger that fires when the data within a child grouper changes
CREATE TRIGGER trigger_update_parent_on_child_update
AFTER UPDATE ON tes_reporting_spec_groupers
FOR EACH ROW EXECUTE FUNCTION update_parent_on_child_change();
