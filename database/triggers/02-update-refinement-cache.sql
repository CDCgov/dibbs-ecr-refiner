-- =============================================================================
-- TRIGGER 2: refinement & caching--this is the final and most critical step. the
-- trigger populates the `refinement_cache` by combining the aggregated "base"
-- codes from a parent grouper with the jurisdiction-specific codes from a user's
-- `configuration`. this trigger is designed to fire in two distinct scenarios:
-- * directly, when a user creates, updates, or deletes a record in the `configurations` table
-- * indirectly, when Trigger 1 updates a parent `tes_condition_grouper`. This change cascades,
--   causing Trigger 2 to re-evaluate and update the cache for every single configuration linked
--   to that parent
-- =============================================================================

CREATE OR REPLACE FUNCTION update_refinement_cache()
RETURNS TRIGGER AS $$
DECLARE
    -- the record variable must be explicitly typed to match the table.
    conf configurations%ROWTYPE;
BEGIN
    -- CASE 1: the change came from a user modifying a configuration.
    IF (TG_TABLE_NAME = 'configurations') THEN
        IF (TG_OP = 'DELETE') THEN
            -- on delete, we need to manually clear the cache.
            -- a simple implementation is to pass the OLD record to the helper,
            -- which will effectively recalculate based on zero addition codes
            PERFORM update_cache_for_configuration(OLD, TRUE);
        ELSE
            PERFORM update_cache_for_configuration(NEW, FALSE);
        END IF;

    -- CASE 2: the change came from an update to the parent grouper itself
    ELSIF (TG_TABLE_NAME = 'tes_condition_groupers' AND TG_OP = 'UPDATE') THEN
        -- loop through every configuration that is a descendant of the updated parent grouper
        FOR conf IN
            SELECT *
            FROM configurations c
            JOIN tes_condition_grouper_references ref
              ON c.child_grouper_url = ref.child_grouper_url
             AND c.child_grouper_version = ref.child_grouper_version
            WHERE ref.parent_grouper_url = NEW.canonical_url
              AND ref.parent_grouper_version = NEW.version
        LOOP
            PERFORM update_cache_for_configuration(conf, FALSE);
        END LOOP;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- helper function to perform the cache update for a single configuration
CREATE OR REPLACE FUNCTION update_cache_for_configuration(conf configurations, is_delete BOOLEAN)
RETURNS void AS $$
DECLARE
    base_codes JSONB;
    addition_codes JSONB;
    combined_codes JSONB;
    child_snomed_code VARCHAR;
    parent_url VARCHAR;
    parent_ver VARCHAR;
BEGIN
    SELECT parent_grouper_url, parent_grouper_version
    INTO parent_url, parent_ver
    FROM tes_condition_grouper_references
    WHERE child_grouper_url = conf.child_grouper_url AND child_grouper_version = conf.child_grouper_version
    LIMIT 1;

    IF NOT FOUND THEN RETURN; END IF;

    SELECT (COALESCE(loinc_codes, '[]'::jsonb) || COALESCE(snomed_codes, '[]'::jsonb) || COALESCE(icd10_codes, '[]'::jsonb) || COALESCE(rxnorm_codes, '[]'::jsonb))
    INTO base_codes
    FROM tes_condition_groupers
    WHERE canonical_url = parent_url AND version = parent_ver;

    -- if the configuration is being deleted, treat its additions as empty.
    IF is_delete THEN
        addition_codes := '[]'::jsonb;
    ELSE
        addition_codes := (COALESCE(conf.loinc_codes, '[]'::jsonb) || COALESCE(conf.snomed_codes, '[]'::jsonb) || COALESCE(conf.icd10_codes, '[]'::jsonb) || COALESCE(conf.rxnorm_codes, '[]'::jsonb));
    END IF;

    SELECT jsonb_agg(DISTINCT value)
    INTO combined_codes
    FROM (
        SELECT jsonb_array_elements_text(base_codes) AS value
        UNION ALL
        SELECT jsonb_array_elements_text(addition_codes)
    ) AS all_codes;

    SELECT snomed_code INTO child_snomed_code FROM tes_reporting_spec_groupers
    WHERE canonical_url = conf.child_grouper_url AND version = conf.child_grouper_version;

    -- "upsert" into the cache
    INSERT INTO refinement_cache (snomed_code, jurisdiction_id, aggregated_codes, source_details)
    VALUES (
        child_snomed_code,
        conf.jurisdiction_id,
        COALESCE(combined_codes, '[]'::jsonb),
        jsonb_build_object(
            'parent_version', parent_ver,
            'child_version', conf.child_grouper_version,
            'configuration_id', conf.id
        )
    )
    ON CONFLICT (snomed_code, jurisdiction_id) DO UPDATE SET
        aggregated_codes = EXCLUDED.aggregated_codes,
        source_details = EXCLUDED.source_details,
        updated_at = now();
END;
$$ LANGUAGE plpgsql;


-- the trigger definitions remain the same
CREATE TRIGGER trigger_update_cache_on_config_change
AFTER INSERT OR UPDATE OR DELETE ON configurations
FOR EACH ROW EXECUTE FUNCTION update_refinement_cache();

CREATE TRIGGER trigger_update_cache_on_grouper_change
AFTER UPDATE ON tes_condition_groupers
FOR EACH ROW EXECUTE FUNCTION update_refinement_cache();
