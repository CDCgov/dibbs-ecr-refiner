-- table for storing groupers with associated codes
CREATE TABLE IF NOT EXISTS groupers (
    condition TEXT PRIMARY KEY,           -- SNOMED code for the condition
    display_name TEXT,                    -- the display name of the condition
    loinc_codes TEXT DEFAULT '[]',        -- JSON array of LOINC codes
    snomed_codes TEXT DEFAULT '[]',       -- JSON array of SNOMED codes
    icd10_codes TEXT DEFAULT '[]',        -- JSON array of ICD-10 codes
    rxnorm_codes TEXT DEFAULT '[]'        -- JSON array of RxNorm codes
);

-- table for storing user-defined filters
CREATE TABLE IF NOT EXISTS filters (
    condition TEXT PRIMARY KEY,           -- Links to condition_code in groupers
    display_name TEXT,                    -- the display name of the condition
    ud_loinc_codes TEXT DEFAULT '[]',     -- JSON array of user-defined LOINC codes
    ud_snomed_codes TEXT DEFAULT '[]',    -- JSON array of user-defined SNOMED codes
    ud_icd10_codes TEXT DEFAULT '[]',     -- JSON array of user-defined ICD-10 codes
    ud_rxnorm_codes TEXT DEFAULT '[]',    -- JSON array of user-defined RxNorm codes
    included_groupers TEXT DEFAULT '[]'   -- JSON array of grouper condition codes
);

-- table for storing local user info --
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- table for storing logged-in user sessions --
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);
