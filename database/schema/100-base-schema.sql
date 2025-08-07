-- drop old objects if they exist, using IF EXISTS to prevent errors on first run.
-- the order is important to respect dependencies.
DROP TABLE IF EXISTS activations;
DROP TABLE IF EXISTS configuration_labels;
DROP TABLE IF EXISTS labels;
DROP TABLE IF EXISTS configurations;
DROP TABLE IF EXISTS conditions;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS jurisdictions;


-- this table stores a list of known jurisdictions
-- * we may want to prepopulate this with a list from APHL that would
-- match the codes we'd see in the RR.
CREATE TABLE jurisdictions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    state_code TEXT
);

-- This table stores user information and links them to a jurisdiction
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    jurisdiction_id TEXT REFERENCES jurisdictions(id)
);

-- this is the core table containing the aggregated, denormalized data for each condition grouper
-- we handle the aggregation of codes from child ValueSets _before_ the seeding
CREATE TABLE conditions (
    canonical_url TEXT NOT NULL,
    version TEXT NOT NULL,
    display_name TEXT,
    child_rsg_snomed_codes TEXT[],
    loinc_codes JSONB,
    snomed_codes JSONB,
    icd10_codes JSONB,
    rxnorm_codes JSONB,
    -- a condition is uniquely identified by its URL and version
    PRIMARY KEY (canonical_url, version)
);

-- a GIN index is highly effective for searching within arrays
CREATE INDEX idx_conditions_child_snomed_codes ON conditions USING GIN (child_rsg_snomed_codes);

-- simplified configurations table - version-centric approach
-- * each row represents a specific, immutable configuration version (like github issues/PRs)
-- * configuration ID becomes the user-facing version number (e.g., "configuration #47")
-- * benefits:
--   - eliminates complex joins
--   - simpler activation lookups
--   - more intuitive user experience ("work with config #47")
--   - matches github's issue numbering paradigm
CREATE TABLE configurations (
    id SERIAL PRIMARY KEY,                    -- This IS the user-facing version number
    jurisdiction_id TEXT NOT NULL REFERENCES jurisdictions(id),
    name TEXT NOT NULL,                       -- Can be renamed anytime without versioning
    description TEXT,

    -- configuration data: references to base conditions by composite key
    -- must reference at least one condition to ensure configurations have meaningful clinical context
    included_conditions JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- structure: [{"canonical_url": "...", "version": "..."}, ...]

    -- jurisdiction-specific code additions (beyond what's in the base conditions)
    loinc_codes_additions JSONB DEFAULT '[]'::jsonb,
    snomed_codes_additions JSONB DEFAULT '[]'::jsonb,
    icd10_codes_additions JSONB DEFAULT '[]'::jsonb,
    rxnorm_codes_additions JSONB DEFAULT '[]'::jsonb,

    -- optional: track relationships between configurations for audit/history
    -- e.g., "configuration #48 was cloned from #47"
    derived_from_id INTEGER REFERENCES configurations(id),

    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- business rule: configurations must reference at least one condition
    -- this ensures every configuration has a meaningful clinical foundation
    CONSTRAINT configurations_must_have_conditions
    CHECK (jsonb_array_length(included_conditions) > 0)
);

-- time-based activations with pre-computed payloads
-- * this table stores the "activation state" of configurations for specific SNOMED codes
-- * key optimization: computed_codes contains pre-aggregated data matching ProcessedGrouper structure
-- * benefits:
--   - runtime queries become simple lookups instead of complex aggregations
--   - predictable performance regardless of configuration complexity
--   - easy to sync with S3 for horizontal scaling via Lambda
--   - full audit trail of activation history
CREATE TABLE activations (
    jurisdiction_id TEXT NOT NULL REFERENCES jurisdictions(id),
    snomed_code TEXT NOT NULL,                -- From conditions.child_rsg_snomed_codes
    configuration_id INTEGER NOT NULL REFERENCES configurations(id),

    -- lifecycle tracking: when was this activated/deactivated
    activated_at TIMESTAMPTZ DEFAULT NOW(),
    -- NULL = currently active
    deactivated_at TIMESTAMPTZ NULL,

    -- pre-computed aggregated codes (replaces complex runtime query)
    -- structure matches ProcessedGrouper for easy consumption by terminology service
    computed_codes JSONB NOT NULL,
    -- example: {"loinc_codes": [...], "snomed_codes": [...], "icd10_codes": [...], "rxnorm_codes": [...]}

    -- S3 synchronization tracking for Lambda-based horizontal scaling
    s3_synced_at TIMESTAMPTZ NULL,
    s3_object_key TEXT NULL,

    -- composite primary key allows for full activation history
    PRIMARY KEY (jurisdiction_id, snomed_code, activated_at)
);

-- business rule: only one active configuration per jurisdiction+snomed combination
-- * this prevents conflicts where multiple configurations could apply to the same condition
CREATE UNIQUE INDEX idx_one_active_per_snomed
ON activations (jurisdiction_id, snomed_code)
WHERE deactivated_at IS NULL;

-- performance optimization for the most common query pattern
-- fast lookup for "what configuration is currently active for this condition?"
CREATE INDEX idx_activations_active_lookup
ON activations (jurisdiction_id, snomed_code)
WHERE deactivated_at IS NULL;

-- this table stores the available labels (tags) for organizing configurations
-- labels can be added/removed from configurations without creating new versions
-- (similar to github issue/PR labels)
CREATE TABLE labels (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    color TEXT, -- e.g., a hex code like '#4287f5'
    description TEXT
);

-- join table for applying multiple labels to configurations
-- works with the simplified configurations table - labels apply to specific configuration versions
CREATE TABLE configuration_labels (
    configuration_id INTEGER NOT NULL REFERENCES configurations(id) ON DELETE CASCADE,
    label_id INTEGER NOT NULL REFERENCES labels(id) ON DELETE CASCADE,
    PRIMARY KEY (configuration_id, label_id)
);
