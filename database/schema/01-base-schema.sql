-- PART 1: user identity and jurisdiction management
CREATE TABLE IF NOT EXISTS jurisdictions (
    id VARCHAR PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    state_code VARCHAR(2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    jurisdiction_id VARCHAR NOT NULL REFERENCES jurisdictions(id),
    full_name VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- PART 2: the "source of truth"--normalized relational model
CREATE TABLE IF NOT EXISTS tes_condition_groupers (
    canonical_url VARCHAR NOT NULL,
    version VARCHAR NOT NULL,
    display_name VARCHAR NOT NULL,
    loinc_codes JSONB,
    snomed_codes JSONB,
    icd10_codes JSONB,
    rxnorm_codes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (canonical_url, version)
);

CREATE TABLE IF NOT EXISTS tes_reporting_spec_groupers (
    canonical_url VARCHAR NOT NULL,
    version VARCHAR NOT NULL,
    display_name VARCHAR,
    snomed_code VARCHAR NOT NULL,
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
    parent_grouper_url VARCHAR NOT NULL,
    parent_grouper_version VARCHAR NOT NULL,
    child_grouper_url VARCHAR NOT NULL,
    child_grouper_version VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_grouper_url, parent_grouper_version) REFERENCES tes_condition_groupers(canonical_url, version) ON DELETE CASCADE,
    FOREIGN KEY (child_grouper_url, child_grouper_version) REFERENCES tes_reporting_spec_groupers(canonical_url, version) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS configurations (
    id SERIAL PRIMARY KEY,
    jurisdiction_id VARCHAR NOT NULL REFERENCES jurisdictions(id),
    child_grouper_url VARCHAR NOT NULL,
    child_grouper_version VARCHAR NOT NULL,
    display_name_override VARCHAR,
    version VARCHAR,
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
    snomed_code VARCHAR NOT NULL,
    jurisdiction_id VARCHAR NOT NULL,
    aggregated_codes JSONB NOT NULL,
    source_details JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (snomed_code, jurisdiction_id)
);
