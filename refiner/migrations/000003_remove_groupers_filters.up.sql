-- this migration simplifies the database schema by removing tables and columns
-- that are either from a legacy data model or are for features that are not yet
-- implemented. this aligns with the principle of not leaving unused artifacts
-- in the database to reduce confusion and technical debt

-- drop legacy tables that have been replaced by the 'conditions' and 'configurations' tables
-- Their presence was for temporary compatibility during development and is no longer needed.
DROP TABLE IF EXISTS public.groupers;
DROP TABLE IF EXISTS public.filters;

-- drop tables related to features that are planned but not yet implemented
-- removing them now provides a clean slate for their future implementation,
-- ensuring the design is not constrained by a pre-existing, unused schema
DROP TABLE IF EXISTS public.activations;
DROP TABLE IF EXISTS public.configuration_labels;
DROP TABLE IF EXISTS public.labels;

-- alter the 'configurations' table to remove columns that are not in use
ALTER TABLE public.configurations
    -- the 'family_id' column and its sequence were part of a versioning concept
    -- that is not currently being used. the current versioning is handled by the
    -- 'version' column alone within the scope of a jurisdiction and name
    DROP COLUMN IF EXISTS family_id,

    -- the 'cloned_from_configuration_id' column was intended for tracking
    -- the provenance of a configuration, a feature that is not implemented
    DROP COLUMN IF EXISTS cloned_from_configuration_id;

-- drop the sequence associated with the removed 'family_id' column.
DROP SEQUENCE IF EXISTS public.configuration_family_id_seq;
