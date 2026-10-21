-- migrate:up

-- ADR 0016 rule 1: one name per concept, and a human-readable label is `display_name`.
-- five tables said `display_name` already while these two said `display` and three
-- columns said `name`; nothing distinguished them semantically.
--
-- the NOT NULL constraints on the renamed columns are renamed with them. that is
-- nominally step 5 of the ADR's sequencing, pulled forward because leaving
-- `codes_name_not_null` attached to a column called `display_name` is worse than
-- either end state. nothing in `app/ ops/ tes/ tests/` references these names by
-- string.
--
-- `codes_value_not_null` and `custom_codes_value_not_null` sit on the `code` columns,
-- stale from before 20260615135704 renamed `value` -> `code`. they are left for step 5.

ALTER TABLE codes
  RENAME COLUMN display TO display_name;

ALTER TABLE custom_codes
  RENAME COLUMN display TO display_name;

-- this row is about a custom code, so the code's label is the row's own label, and
-- the system's label is qualified
ALTER TABLE events_custom_codes
  RENAME COLUMN name TO display_name;
ALTER TABLE events_custom_codes
  RENAME COLUMN system TO system_display_name;

-- `GetConfigurationResponse.display_name` is already built from this column at
-- `api/v1/configurations/base.py`, so this removes an inversion rather than creating one
ALTER TABLE configurations
  RENAME COLUMN name TO display_name;

ALTER TABLE configurations_sections
  RENAME COLUMN name TO display_name;
-- the unique key covers the renamed column, so its name follows. nothing references
-- it by string -- both inserts use a bare `ON CONFLICT DO NOTHING`
ALTER TABLE configurations_sections
  RENAME CONSTRAINT configurations_sections_configuration_id_name_key
                 TO configurations_sections_configuration_id_display_name_key;

-- NOTE: a NOT NULL constraint's name depends on the server, so it is looked up rather
-- than assumed:
-- * before postgres 18 it has no name, and no row in `pg_constraint`; this is a no-op
-- * from 18 it is named for the column as it was when the constraint was created --
--   `codes_name_not_null` on a database built by these migrations, but
--   `codes_display_not_null` on one upgraded from 17 or restored from an older dump
-- each is renamed to the default `<table>_<column>_not_null`, which a dump omits, so
-- `schema.sql` reads the same whichever server produced it
DO $$
DECLARE
  nn record;
BEGIN
  FOR nn IN
    SELECT rel.relname AS table_name, con.conname AS old_name,
           format('%s_%s_not_null', rel.relname, att.attname) AS new_name
    FROM pg_constraint AS con
    JOIN pg_class AS rel ON rel.oid = con.conrelid
    JOIN pg_attribute AS att
      ON att.attrelid = con.conrelid AND att.attnum = con.conkey[1]
    WHERE con.contype = 'n'
      AND rel.relnamespace = 'public'::regnamespace
      AND (rel.relname, att.attname) IN (
        ('codes', 'display_name'),
        ('custom_codes', 'display_name'),
        ('events_custom_codes', 'display_name'),
        ('events_custom_codes', 'system_display_name'),
        ('configurations', 'display_name'),
        ('configurations_sections', 'display_name')
      )
      AND con.conname <> format('%s_%s_not_null', rel.relname, att.attname)
  LOOP
    EXECUTE format(
      'ALTER TABLE %I RENAME CONSTRAINT %I TO %I',
      nn.table_name, nn.old_name, nn.new_name
    );
  END LOOP;
END
$$;


-- migrate:down

-- restores `display`, not the `name` these two carried before
-- 20260615135704_rename_codes_columns.sql
ALTER TABLE codes
  RENAME COLUMN display_name TO display;

ALTER TABLE custom_codes
  RENAME COLUMN display_name TO display;

ALTER TABLE events_custom_codes
  RENAME COLUMN system_display_name TO system;
ALTER TABLE events_custom_codes
  RENAME COLUMN display_name TO name;

ALTER TABLE configurations
  RENAME COLUMN display_name TO name;

ALTER TABLE configurations_sections
  RENAME CONSTRAINT configurations_sections_configuration_id_display_name_key
                 TO configurations_sections_configuration_id_name_key;
ALTER TABLE configurations_sections
  RENAME COLUMN display_name TO name;

-- the same lookup as `migrate:up`, back to the default name for the restored column.
-- on a database built by these migrations that is `codes_display_not_null` rather
-- than the `codes_name_not_null` it started with; the old name was never meaningful,
-- and a default name is the one a dump omits
DO $$
DECLARE
  nn record;
BEGIN
  FOR nn IN
    SELECT rel.relname AS table_name, con.conname AS old_name,
           format('%s_%s_not_null', rel.relname, att.attname) AS new_name
    FROM pg_constraint AS con
    JOIN pg_class AS rel ON rel.oid = con.conrelid
    JOIN pg_attribute AS att
      ON att.attrelid = con.conrelid AND att.attnum = con.conkey[1]
    WHERE con.contype = 'n'
      AND rel.relnamespace = 'public'::regnamespace
      AND (rel.relname, att.attname) IN (
        ('codes', 'display'),
        ('custom_codes', 'display'),
        ('events_custom_codes', 'name'),
        ('events_custom_codes', 'system'),
        ('configurations', 'name'),
        ('configurations_sections', 'name')
      )
      AND con.conname <> format('%s_%s_not_null', rel.relname, att.attname)
  LOOP
    EXECUTE format(
      'ALTER TABLE %I RENAME CONSTRAINT %I TO %I',
      nn.table_name, nn.old_name, nn.new_name
    );
  END LOOP;
END
$$;
