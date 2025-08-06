-- drop old objects if they exist, using IF EXISTS to prevent errors on first run.
-- the order is important to respect dependencies.
DROP TABLE IF EXISTS activations;
DROP TABLE IF EXISTS configuration_labels;
DROP TABLE IF EXISTS labels;
DROP TABLE IF EXISTS configuration_versions;
DROP TABLE IF EXISTS configurations;
DROP TABLE IF EXISTS conditions;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS jurisdictions;
DROP TYPE IF EXISTS configuration_status;


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

-- this table represents a conceptual configuration "idea"
-- for example, "Influenza Surveillance" can have many versions/iterations compared to "Respiratory Surveillance"
CREATE TABLE configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jurisdiction_id TEXT NOT NULL REFERENCES jurisdictions(id),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    -- a jurisdiction can't have two configurations with the same name
    UNIQUE (jurisdiction_id, name)
);

-- a type to represent the lifecycle of a configuration version
-- 'draft': in progress, not ready for use
-- 'active': vetted, approved, and will be used by the activation logic
-- 'archived': no longer in use, kept for historical purposes
CREATE TYPE configuration_status AS ENUM ('draft', 'active', 'archived');

-- this table stores each specific, immutable version of a configuration
-- every time a user saves a change, a new row is created here
CREATE TABLE configuration_versions (
    id SERIAL PRIMARY KEY,
    configuration_id UUID NOT NULL REFERENCES configurations(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    -- the status of the version in its lifecycle
    status configuration_status NOT NULL DEFAULT 'draft',
    -- user notes about what changed in this version
    notes TEXT,

    -- the actual configuration data:
    included_conditions JSONB,
    loinc_codes_additions JSONB,
    snomed_codes_additions JSONB,
    icd10_codes_additions JSONB,
    rxnorm_codes_additions JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- a configuration can't have two versions with the same number
    UNIQUE (configuration_id, version)
);

-- this new table explicitly links an "active" configuration version to a
-- specific SNOMED code that triggers it. This is the heart of the activation logic
CREATE TABLE activations (
  id SERIAL PRIMARY KEY,
  snomed_code TEXT NOT NULL,
  jurisdiction_id TEXT NOT NULL REFERENCES jurisdictions(id),
  configuration_version_id INTEGER NOT NULL REFERENCES configuration_versions(id) ON DELETE CASCADE,
  UNIQUE (jurisdiction_id, snomed_code),  -- Business rule enforcement
  UNIQUE (configuration_version_id, snomed_code, jurisdiction_id)
);

-- optimal indexes for exact-match use case
-- * fast code lookup
CREATE INDEX idx_activations_snomed_code ON activations(snomed_code);
-- * composite queries
CREATE INDEX idx_activations_jurisdiction_snomed ON activations(jurisdiction_id, snomed_code);

-- this table stores the available labels (tags) for organizing configurations
CREATE TABLE labels (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    color TEXT, -- e.g., a hex code like '#4287f5'
    description TEXT
);

-- this is the join table to apply multiple labels to a configuration "idea".
CREATE TABLE configuration_labels (
    configuration_id UUID NOT NULL REFERENCES configurations(id) ON DELETE CASCADE,
    label_id INTEGER NOT NULL REFERENCES labels(id) ON DELETE CASCADE,
    PRIMARY KEY (configuration_id, label_id)
);
