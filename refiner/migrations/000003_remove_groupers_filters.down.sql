-- re-create the sequence for 'family_id' before it's referenced in the table alteration
CREATE SEQUENCE public.configuration_family_id_seq START 1000 INCREMENT 1;

-- re-add the removed columns to the 'configurations' table with their original definitions
ALTER TABLE public.configurations
    -- restore 'family_id' column and set its default to use the re-created sequence
    ADD COLUMN family_id INTEGER NOT NULL DEFAULT nextval('configuration_family_id_seq'),

    -- restore 'cloned_from_configuration_id' column with its foreign key constraint
    ADD COLUMN cloned_from_configuration_id UUID REFERENCES configurations(id);

-- re-create the 'labels' table for tagging configurations
CREATE TABLE public.labels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    color TEXT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- re-create the join table for applying labels to configurations
-- this depends on the 'labels' and 'configurations' tables
CREATE TABLE public.configuration_labels (
    configuration_id UUID NOT NULL REFERENCES configurations(id) ON DELETE CASCADE,
    label_id UUID NOT NULL REFERENCES labels(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (configuration_id, label_id)
);

-- re-create the 'activations' table for managing active configurations
-- this depends on the 'jurisdictions' and 'configurations' tables
CREATE TABLE public.activations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jurisdiction_id TEXT NOT NULL REFERENCES jurisdictions(id),
    snomed_code TEXT NOT NULL,
    configuration_id UUID NOT NULL REFERENCES configurations(id),
    activated_at TIMESTAMPTZ DEFAULT NOW(),
    deactivated_at TIMESTAMPTZ NULL,
    computed_codes JSONB NOT NULL,
    s3_synced_at TIMESTAMPTZ NOT NULL,
    s3_object_key TEXT NOT NULL
);

-- re-create the indexes on the 'activations' table
CREATE UNIQUE INDEX idx_one_active_per_snomed
ON public.activations (jurisdiction_id, snomed_code)
WHERE deactivated_at IS NULL;

CREATE INDEX idx_activations_active_lookup
ON public.activations (jurisdiction_id, snomed_code)
WHERE deactivated_at IS NULL;


-- re-create the legacy 'filters' table
CREATE TABLE public.filters (
    condition TEXT PRIMARY KEY,
    display_name TEXT,
    ud_loinc_codes TEXT DEFAULT '[]',
    ud_snomed_codes TEXT DEFAULT '[]',
    ud_icd10_codes TEXT DEFAULT '[]',
    ud_rxnorm_codes TEXT DEFAULT '[]',
    included_groupers TEXT DEFAULT '[]'
);

-- re-create the legacy 'groupers' table
CREATE TABLE public.groupers (
    condition TEXT PRIMARY KEY,
    display_name TEXT,
    loinc_codes TEXT DEFAULT '[]',
    snomed_codes TEXT DEFAULT '[]',
    icd10_codes TEXT DEFAULT '[]',
    rxnorm_codes TEXT DEFAULT '[]'
);
