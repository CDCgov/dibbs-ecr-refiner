-- migrate:up

-- Sections the eICR IG defines trigger code templates for cannot be removed:
-- removing a section strips every <entry> it holds, so a configuration that
-- removed them all would emit a document carrying no trigger codes and fail
-- Schematron validation. See TriggerCodeSection in app/services/ecr/policy.py --
-- this list is the union across every supported eICR version and must stay in
-- sync with that enum.
--
-- The include toggle was previously unconstrained for these codes, so drafts
-- authored before the policy landed may hold include = false. Those rows are
-- unreachable through the product now that the UI greys the toggle out, so they
-- are corrected here.
--
-- Scoped to drafts deliberately. Active and inactive configurations serialize
-- their sections to S3 at activation time, and this migration does not rewrite
-- those files, so correcting their rows would change nothing about how they
-- refine today. They are covered instead by normalization at the two paths that
-- can carry a stale row forward: clone_section_processing_instructions when a
-- new version is drafted, and convert_config_to_storage_payload when a
-- configuration is activated.

UPDATE configurations_sections s
SET include = true
FROM configurations c
WHERE c.id = s.configuration_id
  AND c.status = 'draft'
  AND s.include = false
  AND s.section_type = 'standard'
  AND s.code IN (
    '10160-0', -- Medications
    '11369-6', -- Immunizations
    '11450-4', -- Problem
    '18776-5', -- Plan of Treatment
    '29549-3', -- Medications Administered
    '30954-2', -- Results
    '42346-7', -- Admission Medications
    '46240-8', -- Encounters
    '47519-4'  -- Procedures
  );

-- migrate:down

-- Irreversible by design: the pre-migration include value is not recorded, so
-- there is nothing to restore it from. Rolling back leaves the corrected rows
-- in place, which remains the safe state.
