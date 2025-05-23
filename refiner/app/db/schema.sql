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
