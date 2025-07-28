-- =============================================================================
-- TRIGGER 2: populate the denormalized runtime cache
--
-- this trigger populates the `refinement_cache` by combining aggregated "base"
-- codes from a parent grouper with jurisdiction-specific user defined codes from
-- a user's `configuration`. it fires in two scenarios:
--   1. directly, when a user changes a record in the `configurations` table.
--   2. indirectly, when Trigger 1 updates a parent `tes_condition_grouper`
--
-- the core logic is delegated to the `update_cache_for_configuration` helper
-- =============================================================================

-- this is the main trigger function attached to the tables
-- its only job is to figure out WHICH configuration(s) need updating
CREATE OR REPLACE FUNCTION update_refinement_cache()
RETURNS TRIGGER AS $$
DECLARE
    conf configurations%ROWTYPE;
BEGIN
    IF (TG_TABLE_NAME = 'configurations') THEN
        -- CASE 1: a configuration was changed; update this single cache entry
        -- COALESCE handles INSERT, UPDATE, and DELETE in one line
        PERFORM update_cache_for_configuration(COALESCE(NEW, OLD));

    ELSIF (TG_TABLE_NAME = 'tes_condition_groupers' AND TG_OP = 'UPDATE') THEN
        -- CASE 2: the base data in a parent grouper changed
        -- we must find and update ALL configurations linked to this parent
        FOR conf IN
            SELECT c.*
            FROM configurations c
            JOIN tes_condition_grouper_references ref
              ON c.child_grouper_url = ref.child_grouper_url AND c.child_grouper_version = ref.child_grouper_version
            WHERE ref.parent_grouper_url = NEW.canonical_url AND ref.parent_grouper_version = NEW.version
        LOOP
            PERFORM update_cache_for_configuration(conf);
        END LOOP;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


-- this helper function contains the actual logic to update one cache entry
CREATE OR REPLACE FUNCTION update_cache_for_configuration(conf configurations)
RETURNS void AS $$
DECLARE
    base_codes TEXT[];
    addition_codes TEXT[];
    combined_codes TEXT[];
    parent_grouper tes_condition_groupers;
    child_snomed_code TEXT;
BEGIN
    -- Step 1: find the parent grouper record associated with this configuration
    SELECT g.* INTO parent_grouper
    FROM tes_condition_groupers g
    JOIN tes_condition_grouper_references ref
      ON g.canonical_url = ref.parent_grouper_url AND g.version = ref.parent_grouper_version
    WHERE ref.child_grouper_url = conf.child_grouper_url AND ref.child_grouper_version = conf.child_grouper_version
    LIMIT 1;

    IF NOT FOUND THEN RETURN; END IF;

    -- Step 2: use the helper function to flatten all codes from the parent and the config
    base_codes := get_all_codes_from_grouper(parent_grouper);
    addition_codes := get_all_codes_from_grouper(conf);

    -- Step 3: combine the two sets of codes and de-duplicate them
    SELECT array_agg(DISTINCT code)
    INTO combined_codes
    FROM (
        SELECT unnest(base_codes)
        UNION ALL
        SELECT unnest(addition_codes)
    ) AS all_codes(code);

    -- Step 4: get the child's SNOMED code, which is part of the cache's primary key
    SELECT snomed_code INTO child_snomed_code FROM tes_reporting_spec_groupers
    WHERE canonical_url = conf.child_grouper_url AND version = conf.child_grouper_version;

    -- Step 5: "upsert" the final, combined data into the cache table
    INSERT INTO refinement_cache (snomed_code, jurisdiction_id, aggregated_codes, source_details)
    VALUES (
        child_snomed_code, conf.jurisdiction_id, COALESCE(combined_codes, ARRAY[]::TEXT[]),
        jsonb_build_object('parent_version', parent_grouper.version, 'child_version', conf.child_grouper_version, 'configuration_id', conf.id)
    )
    ON CONFLICT (snomed_code, jurisdiction_id) DO UPDATE SET
        aggregated_codes = EXCLUDED.aggregated_codes, source_details = EXCLUDED.source_details, updated_at = now();
END;
$$ LANGUAGE plpgsql;

-- create a trigger that fires when a user configuration changes
CREATE TRIGGER trigger_update_cache_on_config_change
AFTER INSERT OR UPDATE OR DELETE ON configurations
FOR EACH ROW EXECUTE FUNCTION update_refinement_cache();

-- create a trigger that fires when the aggregated base data changes
CREATE TRIGGER trigger_update_cache_on_grouper_change
AFTER UPDATE ON tes_condition_groupers
FOR EACH ROW EXECUTE FUNCTION update_refinement_cache();
