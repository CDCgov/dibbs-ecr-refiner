-- this migration simplifies the database schema by removing tables and columns
-- that are either from a legacy data model or are for features that are not yet
-- implemented. this aligns with the principle of not leaving unused artifacts
-- in the database to reduce confusion and technical debt

-- drop legacy tables that have been replaced by the 'conditions' and 'configurations' tables
-- Their presence was for temporary compatibility during development and is no longer needed.
DROP TABLE groupers;
DROP TABLE filters;

-- drop tables related to features that are planned but not yet implemented
-- removing them now provides a clean slate for their future implementation,
-- ensuring the design is not constrained by a pre-existing, unused schema
DROP TABLE activations;
DROP TABLE configuration_labels;
DROP TABLE labels;

-- alter the 'configurations' table to remove columns that are not in use
ALTER TABLE configurations
    -- the 'family_id' column and its sequence were part of a versioning concept
    -- that is not currently being used. the current versioning is handled by the
    -- 'version' column alone within the scope of a jurisdiction and name
    DROP COLUMN family_id,

    -- the 'cloned_from_configuration_id' column was intended for tracking
    -- the provenance of a configuration, a feature that is not implemented
    DROP COLUMN cloned_from_configuration_id,

    -- drop the sections_to_include column
    -- rather than cast an empty column to jsonb for section
    -- processing instructions as jsonb this will make the
    -- migration logic a lot simpler (see below)
    DROP COLUMN sections_to_include;

-- drop the sequence associated with the removed 'family_id' column.
DROP SEQUENCE configuration_family_id_seq;

-- add the new section_processing column as jsonb, default empty object
ALTER TABLE configurations
    -- the idea for this lis that it would end upooking like:
    -- {
    --   display_name: 'Social History',
    --   code: '29762-2',
    --   action: 'retain'
    -- },
    -- actions can be: retain, refine, remove
    ADD COLUMN section_processing jsonb DEFAULT '{}'::jsonb;
