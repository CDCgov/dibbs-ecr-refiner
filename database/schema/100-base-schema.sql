-- drop old tables if they exist, using IF EXISTS to prevent errors on first run.
-- the order is important to respect foreign key constraints.
DROP TABLE IF EXISTS configuration_labels;
DROP TABLE IF EXISTS labels;
DROP TABLE IF EXISTS configuration_versions;
DROP TABLE IF EXISTS configurations;
DROP TABLE IF EXISTS conditions;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS jurisdictions;

-- this table stores a list of known jurisdictions
-- we may want to prepopulate this with a list from APHL that would
-- match the codes we'd see in the RR
CREATE TABLE jurisdictions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    state_code TEXT
);

-- this table stores user information and links them to a jurisdiction
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    jurisdiction_id TEXT REFERENCES jurisdictions(id)
);

-- this is the core table containing the aggregated, denormalized data
-- for each condition grouper and version we'll assocaite the individual
-- rs-grouper SNOMED codes as an array and handle the aggregation _before_
-- the seeding
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
    -- we can also use _just_ the uuid part of the url too
    PRIMARY KEY (canonical_url, version)
);

CREATE INDEX idx_conditions_child_snomed_codes ON conditions USING GIN (child_rsg_snomed_codes);

-- this table represents a conceptual configuration "idea"
-- for example, "influenza + RSV" can have many versions/iterations
-- and the versions
CREATE TABLE configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jurisdiction_id TEXT NOT NULL REFERENCES jurisdictions(id),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    -- a jurisdiction can't have two configurations with the same name.
    UNIQUE (jurisdiction_id, name)
);

-- this table stores each specific, immutable version of a configuration
-- every time a user saves a change, a new row is created here
CREATE TABLE configuration_versions (
    id SERIAL PRIMARY KEY,
    configuration_id UUID NOT NULL REFERENCES configurations(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    -- the "ready for production" flag
    is_active BOOLEAN DEFAULT FALSE,
    -- user notes about what changed in this version
    notes TEXT,

    -- the actual configuration data:
    included_conditions JSONB,
    loinc_codes_additions JSONB,
    snomed_codes_additions JSONB,
    icd10_codes_additions JSONB,
    rxnorm_codes_additions JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- a configuration group can't have two versions with the same number
    UNIQUE (configuration_id, version)
);

-- this partial index ensures that for any given configuration group,
-- only ONE version can be marked as active (ready for production)
CREATE UNIQUE INDEX one_active_version_per_configuration ON configuration_versions (configuration_id) WHERE is_active;

-- this table stores the available labels (tags)
CREATE TABLE labels (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    color TEXT, -- e.g., a hex code like '#4287f5'
    description TEXT
);

-- this is the join table to apply multiple labels to a configuration "idea"
CREATE TABLE configuration_labels (
    configuration_id UUID NOT NULL REFERENCES configurations(id) ON DELETE CASCADE,
    label_id INTEGER NOT NULL REFERENCES labels(id) ON DELETE CASCADE,
    PRIMARY KEY (configuration_id, label_id)
);
