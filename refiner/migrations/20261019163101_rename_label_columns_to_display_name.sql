-- migrate:up

-- ADR 0016 rule 1: one name per concept, and a human-readable label is `display_name`.
-- five tables said `display_name` already while these two said `display` and three
-- columns said `name`; nothing distinguished them semantically.
--
-- five `*_name_not_null` constraints are renamed with their columns. that is nominally
-- step 5 of the ADR's sequencing, pulled forward because leaving
-- `codes_name_not_null` attached to a column called `display_name` is worse than
-- either end state, and it is free in the same statement. nothing in
-- `app/ ops/ tes/ tests/` references these names by string.
--
-- `codes_value_not_null` and `custom_codes_value_not_null` sit on the `code` columns,
-- stale from before 20260615135704 renamed `value` -> `code`. they are left for step 5.
--
-- postgres omits a NOT NULL constraint's name from a dump when it matches the default
-- `<table>_<column>_not_null`, so a correct rename here makes these disappear from
-- `schema.sql` rather than appear in it.

ALTER TABLE codes
  RENAME COLUMN display TO display_name;
ALTER TABLE codes
  RENAME CONSTRAINT codes_name_not_null TO codes_display_name_not_null;

ALTER TABLE custom_codes
  RENAME COLUMN display TO display_name;
ALTER TABLE custom_codes
  RENAME CONSTRAINT custom_codes_name_not_null TO custom_codes_display_name_not_null;

-- this row is about a custom code, so the code's label is the row's own label, and
-- the system's label is qualified
ALTER TABLE events_custom_codes
  RENAME COLUMN name TO display_name;
ALTER TABLE events_custom_codes
  RENAME CONSTRAINT events_custom_code_uploads_name_not_null
                 TO events_custom_codes_display_name_not_null;
ALTER TABLE events_custom_codes
  RENAME COLUMN system TO system_display_name;
ALTER TABLE events_custom_codes
  RENAME CONSTRAINT events_custom_code_uploads_system_not_null
                 TO events_custom_codes_system_display_name_not_null;

-- `GetConfigurationResponse.display_name` is already built from this column at
-- `api/v1/configurations/base.py`, so this removes an inversion rather than creating one
ALTER TABLE configurations
  RENAME COLUMN name TO display_name;
ALTER TABLE configurations
  RENAME CONSTRAINT configurations_name_not_null
                 TO configurations_display_name_not_null;

ALTER TABLE configurations_sections
  RENAME COLUMN name TO display_name;
ALTER TABLE configurations_sections
  RENAME CONSTRAINT configurations_sections_name_not_null
                 TO configurations_sections_display_name_not_null;
-- the unique key covers the renamed column, so its name follows. nothing references
-- it by string -- both inserts use a bare `ON CONFLICT DO NOTHING`
ALTER TABLE configurations_sections
  RENAME CONSTRAINT configurations_sections_configuration_id_name_key
                 TO configurations_sections_configuration_id_display_name_key;


-- migrate:down

-- restores `display`, not the `name` these two carried before
-- 20260615135704_rename_codes_columns.sql
ALTER TABLE codes
  RENAME CONSTRAINT codes_display_name_not_null TO codes_name_not_null;
ALTER TABLE codes
  RENAME COLUMN display_name TO display;

ALTER TABLE custom_codes
  RENAME CONSTRAINT custom_codes_display_name_not_null TO custom_codes_name_not_null;
ALTER TABLE custom_codes
  RENAME COLUMN display_name TO display;

ALTER TABLE events_custom_codes
  RENAME CONSTRAINT events_custom_codes_system_display_name_not_null
                 TO events_custom_code_uploads_system_not_null;
ALTER TABLE events_custom_codes
  RENAME COLUMN system_display_name TO system;
ALTER TABLE events_custom_codes
  RENAME CONSTRAINT events_custom_codes_display_name_not_null
                 TO events_custom_code_uploads_name_not_null;
ALTER TABLE events_custom_codes
  RENAME COLUMN display_name TO name;

ALTER TABLE configurations
  RENAME CONSTRAINT configurations_display_name_not_null
                 TO configurations_name_not_null;
ALTER TABLE configurations
  RENAME COLUMN display_name TO name;

ALTER TABLE configurations_sections
  RENAME CONSTRAINT configurations_sections_configuration_id_display_name_key
                 TO configurations_sections_configuration_id_name_key;
ALTER TABLE configurations_sections
  RENAME CONSTRAINT configurations_sections_display_name_not_null
                 TO configurations_sections_name_not_null;
ALTER TABLE configurations_sections
  RENAME COLUMN display_name TO name;
