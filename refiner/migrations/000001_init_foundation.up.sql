-- table for storing groupers with associated codes
CREATE TABLE groupers (
    condition TEXT PRIMARY KEY,           -- SNOMED code for the condition
    display_name TEXT,                    -- the display name of the condition
    loinc_codes TEXT DEFAULT '[]',        -- JSON array of LOINC codes
    snomed_codes TEXT DEFAULT '[]',       -- JSON array of SNOMED codes
    icd10_codes TEXT DEFAULT '[]',        -- JSON array of ICD-10 codes
    rxnorm_codes TEXT DEFAULT '[]'        -- JSON array of RxNorm codes
);

-- table for storing user-defined filters
CREATE TABLE filters (
    condition TEXT PRIMARY KEY,           -- Links to condition_code in groupers
    display_name TEXT,                    -- the display name of the condition
    ud_loinc_codes TEXT DEFAULT '[]',     -- JSON array of user-defined LOINC codes
    ud_snomed_codes TEXT DEFAULT '[]',    -- JSON array of user-defined SNOMED codes
    ud_icd10_codes TEXT DEFAULT '[]',     -- JSON array of user-defined ICD-10 codes
    ud_rxnorm_codes TEXT DEFAULT '[]',    -- JSON array of user-defined RxNorm codes
    included_groupers TEXT DEFAULT '[]'   -- JSON array of grouper condition codes
);

-- new stuff --

-- drop old objects if they exist, using IF EXISTS to prevent errors on first run.
-- the order is important to respect dependencies.


-- this table stores a list of known jurisdictions
-- * we may want to prepopulate this with a list from APHL that would
--   match the codes we'd see in the RR
-- * we are not using a uuid for the pk for this table because the
--   jurisdiction_id is intended to match the same field in the RR
CREATE TABLE jurisdictions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    state_code TEXT
);

-- This table stores user information and links them to a jurisdiction
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    -- full_name TEXT,
    jurisdiction_id TEXT REFERENCES jurisdictions(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- table for storing logged-in user sessions --
CREATE TABLE sessions (
    token_hash TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

-- this is the core table containing the aggregated, denormalized data for each condition grouper
-- we handle the aggregation of codes from child ValueSets _before_ the seeding
CREATE TABLE conditions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_url TEXT NOT NULL,
    version TEXT NOT NULL,
    display_name TEXT,
    child_rsg_snomed_codes TEXT[],
    loinc_codes JSONB,
    snomed_codes JSONB,
    icd10_codes JSONB,
    rxnorm_codes JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    -- a condition is uniquely identified by its URL and version
    UNIQUE (canonical_url, version)
);

-- a GIN index is highly effective for searching within arrays
CREATE INDEX idx_conditions_child_snomed_codes ON conditions USING GIN (child_rsg_snomed_codes);

-- sequence for generating human-readable family IDs (starts at 1000 for professional appearance)
CREATE SEQUENCE configuration_family_id_seq START 1000 INCREMENT 1;

-- simplified configurations table with family/version approach
-- * family_id groups related configuration versions (human-readable: 1001, 1002, etc.)
-- * version tracks iterations within a family (1, 2, 3, etc.)
-- * supports A/B testing: multiple families can target the same condition
-- * benefits:
--   - user-friendly identifiers ("Configuration 1001 v2")
--   - clear version progression within families
--   - ability to test different approaches for same condition
--   - simple activation lookups via UUID primary key
CREATE TABLE configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    family_id INTEGER NOT NULL DEFAULT nextval('configuration_family_id_seq'),
    version INTEGER NOT NULL,
    jurisdiction_id TEXT NOT NULL REFERENCES jurisdictions(id),
    name TEXT NOT NULL,
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

    -- local codes that don't fit standard terminology systems
    -- structure: [{"code": "...", "display": "...", "description": "..."}, ...]
    custom_codes JSONB DEFAULT '[]'::jsonb,

    -- eICR sections to include in processing (array of LOINC codes)
    -- used by server to determine which parts of eICR to include without processing
    sections_to_include TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- if the configuration was "cloned" from another configuration, point to the configuration uuid
    -- * we get history from family_id for free; this will solidify the chain of provenance
    cloned_from_configuration_id UUID REFERENCES configurations(id),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- business rule: configurations must reference at least one condition
    -- this ensures every configuration has a meaningful clinical foundation
    CONSTRAINT configurations_must_have_conditions
    CHECK (jsonb_array_length(included_conditions) > 0),

    -- unique version per family
    UNIQUE(family_id, version)
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jurisdiction_id TEXT NOT NULL REFERENCES jurisdictions(id),
    -- from conditions.child_rsg_snomed_codes
    snomed_code TEXT NOT NULL,
    configuration_id UUID NOT NULL REFERENCES configurations(id),

    -- lifecycle tracking: when was this activated/deactivated
    activated_at TIMESTAMPTZ DEFAULT NOW(),
    deactivated_at TIMESTAMPTZ NULL,                         -- NULL = currently active

    -- pre-computed aggregated codes (replaces complex runtime query)
    -- structure matches ProcessedGrouper for easy consumption by terminology service
    -- * example: {"loinc_codes": [...], "snomed_codes": [...], "icd10_codes": [...], "rxnorm_codes": [...]}
    computed_codes JSONB NOT NULL,

    -- S3 synchronization tracking for lambda based application
    -- both fields are required once activation is complete
    -- the proposed process:
    --   - generate ProcessedGrouper json
    --   - write to activations table
    --   - write to S3
    --   - verify sync
    --   - only then tell user "success"
    s3_synced_at TIMESTAMPTZ NOT NULL,
    s3_object_key TEXT NOT NULL
);

-- business rule: only one active configuration per jurisdiction+snomed combination
-- this prevents conflicts where multiple configurations could apply to the same condition
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    -- e.g., a hex code like '#4287f5'
    color TEXT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- join table for applying multiple labels to individual configurations
-- works with the UUID-based configurations table - labels apply to specific configuration versions
CREATE TABLE configuration_labels (
    configuration_id UUID NOT NULL REFERENCES configurations(id) ON DELETE CASCADE,
    label_id UUID NOT NULL REFERENCES labels(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (configuration_id, label_id)
);

-- Simple function to automatically update the updated_at timestamp
-- This function is intentionally kept very simple for easy understanding and maintenance
CREATE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Automatically update updated_at timestamp on record modification
-- These triggers ensure data consistency without application-level code

CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER update_conditions_updated_at
BEFORE UPDATE ON conditions
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER update_configurations_updated_at
BEFORE UPDATE ON configurations
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER update_labels_updated_at
BEFORE UPDATE ON labels
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
