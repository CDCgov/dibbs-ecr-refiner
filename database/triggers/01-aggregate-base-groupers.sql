-- =============================================================================
-- TRIGGER 1: aggregate base groupers
--
-- this trigger keeps the parent `tes_condition_groupers` table in sync with
-- its children. it fires in two scenarios:
--   1. when a reference between a parent and child is changed
--   2. when the data within a child `tes_reporting_spec_groupers` is updated
--
-- it uses the `get_aggregated_child_codes` helper function to perform the
-- actual aggregation of codes into the parent's JSONB columns
-- =============================================================================

CREATE OR REPLACE FUNCTION update_parent_on_child_change()
RETURNS TRIGGER AS $$
DECLARE
    parent_url_to_update TEXT;
    parent_version_to_update TEXT;
BEGIN
    -- determine which parent needs updating based on what triggered the function
    IF (TG_TABLE_NAME = 'tes_condition_grouper_references') THEN
        -- CASE 1: a reference was inserted, updated, or deleted
        -- the parent's identity is in the NEW or OLD reference row itself
        parent_url_to_update := COALESCE(NEW.parent_grouper_url, OLD.parent_grouper_url);
        parent_version_to_update := COALESCE(NEW.parent_grouper_version, OLD.parent_grouper_version);

    ELSIF (TG_TABLE_NAME = 'tes_reporting_spec_groupers' AND TG_OP = 'UPDATE') THEN
        -- CASE 2: a child RS grouper's codes were updated directly
        -- we must look up the parent in the references table
        SELECT parent_grouper_url, parent_grouper_version
        INTO parent_url_to_update, parent_version_to_update
        FROM tes_condition_grouper_references
        WHERE child_grouper_url = NEW.canonical_url AND child_grouper_version = NEW.version
        LIMIT 1;
    END IF;

    -- if we found a parent, proceed with the update
    IF parent_url_to_update IS NOT NULL THEN
        -- call the helper function for each code type to get the aggregated list
        UPDATE tes_condition_groupers
        SET
            loinc_codes = get_aggregated_child_codes(parent_url_to_update, parent_version_to_update, 'loinc_codes'),
            snomed_codes = get_aggregated_child_codes(parent_url_to_update, parent_version_to_update, 'snomed_codes'),
            icd10_codes = get_aggregated_child_codes(parent_url_to_update, parent_version_to_update, 'icd10_codes'),
            rxnorm_codes = get_aggregated_child_codes(parent_url_to_update, parent_version_to_update, 'rxnorm_codes')
        WHERE canonical_url = parent_url_to_update AND version = parent_version_to_update;
    END IF;

    -- the trigger is an AFTER trigger, so we return NULL
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
