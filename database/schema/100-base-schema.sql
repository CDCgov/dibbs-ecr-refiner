-- PART 1: user identity and jurisdiction management
CREATE TABLE IF NOT EXISTS jurisdictions (
    id VARCHAR(4) PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    state_code VARCHAR(2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    jurisdiction_id VARCHAR(4) NOT NULL REFERENCES jurisdictions(id),
    full_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- PART 2: the "source of truth"--normalized relational model
CREATE TABLE IF NOT EXISTS tes_condition_groupers (
    canonical_url TEXT NOT NULL,
    version TEXT NOT NULL,
    display_name TEXT NOT NULL,
    loinc_codes JSONB,
    snomed_codes JSONB,
    icd10_codes JSONB,
    rxnorm_codes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (canonical_url, version)
);

CREATE TABLE IF NOT EXISTS tes_reporting_spec_groupers (
    canonical_url TEXT NOT NULL,
    version TEXT NOT NULL,
    display_name TEXT,
    snomed_code TEXT NOT NULL,
    loinc_codes JSONB,
    snomed_codes JSONB,
    icd10_codes JSONB,
    rxnorm_codes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (canonical_url, version),
    UNIQUE (snomed_code, version)
);

CREATE TABLE IF NOT EXISTS tes_condition_grouper_references (
    id SERIAL PRIMARY KEY,
    parent_grouper_url TEXT NOT NULL,
    parent_grouper_version TEXT NOT NULL,
    child_grouper_url TEXT NOT NULL,
    child_grouper_version TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_grouper_url, parent_grouper_version) REFERENCES tes_condition_groupers(canonical_url, version) ON DELETE CASCADE,
    FOREIGN KEY (child_grouper_url, child_grouper_version) REFERENCES tes_reporting_spec_groupers(canonical_url, version) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS configurations (
    id SERIAL PRIMARY KEY,
    jurisdiction_id VARCHAR(4) NOT NULL REFERENCES jurisdictions(id),
    child_grouper_url TEXT NOT NULL,
    child_grouper_version TEXT NOT NULL,
    display_name_override TEXT,
    version TEXT,
    loinc_codes JSONB,
    snomed_codes JSONB,
    icd10_codes JSONB,
    rxnorm_codes JSONB,
    is_active BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (child_grouper_url, child_grouper_version) REFERENCES tes_reporting_spec_groupers(canonical_url, version) ON DELETE CASCADE
);

-- PART 3: the "serving layer"--denormalized runtime cache
CREATE TABLE IF NOT EXISTS refinement_cache (
    snomed_code TEXT NOT NULL,
    jurisdiction_id VARCHAR(4) NOT NULL,
    aggregated_codes TEXT[] NOT NULL,
    source_details JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (snomed_code, jurisdiction_id)
);
