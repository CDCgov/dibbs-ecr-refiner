-- migrate:up
CREATE TYPE configuration_status AS ENUM (
    'active',
    'inactive',
    'draft'
);

CREATE TYPE event_type_enum AS ENUM (
    'create_configuration',
    'activate_configuration',
    'deactivate_configuration',
    'add_code',
    'delete_code',
    'edit_code',
    'section_update',
    'lock_acquire',
    'lock_release',
    'lock_renew'
);

CREATE FUNCTION configurations_set_condition_canonical_url_on_insert() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  -- grab canonical_url from conditions when inserting or updating condition_id
  SELECT canonical_url
  INTO NEW.condition_canonical_url
  FROM conditions
  WHERE id = NEW.condition_id
  LIMIT 1;

  RETURN NEW;
END;
$$;

CREATE FUNCTION configurations_set_last_activated_at_on_status_change() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  -- when going from any status to "active" we update `last_activated_at`
  IF NEW.status = 'active' AND OLD.status IS DISTINCT FROM 'active' THEN
    NEW.last_activated_at := NOW();
  END IF;

  RETURN NEW;
END;
$$;

CREATE FUNCTION configurations_set_version_on_insert() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  max_version INTEGER;
BEGIN
  -- find the highest version for the condition/jurisdiction pair
  SELECT MAX(version)
  INTO max_version
  FROM configurations
  WHERE condition_canonical_url = NEW.condition_canonical_url
    AND jurisdiction_id = NEW.jurisdiction_id;

  -- if none exist yet, start at 1 otherwise increment previous max
  IF max_version IS NULL THEN
    NEW.version := 1;
  ELSE
    NEW.version := max_version + 1;
  END IF;

  RETURN NEW;
END;
$$;

CREATE FUNCTION set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

CREATE TABLE conditions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    canonical_url text NOT NULL,
    version text NOT NULL,
    display_name text,
    child_rsg_snomed_codes text[],
    loinc_codes jsonb,
    snomed_codes jsonb,
    icd10_codes jsonb,
    rxnorm_codes jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    PRIMARY KEY (id),
    UNIQUE (canonical_url, version)
);

CREATE TABLE jurisdictions (
    id text NOT NULL,
    name text NOT NULL,
    state_code text,
    PRIMARY KEY (id)
);

CREATE TABLE users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    username text NOT NULL,
    email text NOT NULL,
    jurisdiction_id text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (email),
    UNIQUE (username)
);

CREATE TABLE configurations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    version integer NOT NULL,
    jurisdiction_id text NOT NULL,
    name text NOT NULL,
    included_conditions jsonb DEFAULT '[]'::jsonb NOT NULL,
    custom_codes jsonb DEFAULT '[]'::jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    condition_id uuid NOT NULL,
    section_processing jsonb DEFAULT '[]'::jsonb,
    status configuration_status DEFAULT 'draft'::configuration_status NOT NULL,
    last_activated_at timestamp with time zone,
    last_activated_by uuid,
    condition_canonical_url text NOT NULL,
    created_by uuid NOT NULL,
    s3_urls text[],
    PRIMARY KEY (id),
    UNIQUE (condition_canonical_url, jurisdiction_id, version),
    CONSTRAINT section_processing_must_be_json_array CHECK ((jsonb_typeof(section_processing) = 'array'::text))
);

CREATE TABLE configurations_locks (
    configuration_id uuid NOT NULL,
    user_id uuid NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    PRIMARY KEY (configuration_id)
);

CREATE TABLE events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    jurisdiction_id text NOT NULL,
    user_id uuid NOT NULL,
    configuration_id uuid NOT NULL,
    event_type event_type_enum NOT NULL,
    action_text text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE sessions (
    token_hash text NOT NULL,
    user_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    PRIMARY KEY (token_hash)
);

CREATE UNIQUE INDEX configurations_one_active_per_pair_idx ON configurations USING btree (condition_canonical_url, jurisdiction_id) WHERE (status = 'active'::configuration_status);

CREATE UNIQUE INDEX configurations_one_draft_per_pair_idx ON configurations USING btree (condition_canonical_url, jurisdiction_id) WHERE (status = 'draft'::configuration_status);

CREATE INDEX idx_conditions_child_snomed_codes ON conditions USING gin (child_rsg_snomed_codes);

CREATE TRIGGER configurations_set_condition_canonical_url_trigger BEFORE INSERT OR UPDATE OF condition_id ON configurations FOR EACH ROW EXECUTE FUNCTION configurations_set_condition_canonical_url_on_insert();

CREATE TRIGGER configurations_set_last_activated_at_on_status_change_trigger BEFORE UPDATE OF status ON configurations FOR EACH ROW EXECUTE FUNCTION configurations_set_last_activated_at_on_status_change();

CREATE TRIGGER configurations_set_version_on_insert_trigger BEFORE INSERT ON configurations FOR EACH ROW EXECUTE FUNCTION configurations_set_version_on_insert();

CREATE TRIGGER update_conditions_updated_at BEFORE UPDATE ON conditions FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER update_configurations_updated_at BEFORE UPDATE ON configurations FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION set_updated_at();

ALTER TABLE ONLY configurations
    ADD CONSTRAINT configurations_condition_id_fkey FOREIGN KEY (condition_id) REFERENCES conditions(id);

ALTER TABLE ONLY configurations
    ADD CONSTRAINT configurations_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);

ALTER TABLE ONLY configurations
    ADD CONSTRAINT configurations_jurisdiction_id_fkey FOREIGN KEY (jurisdiction_id) REFERENCES jurisdictions(id);

ALTER TABLE ONLY configurations
    ADD CONSTRAINT configurations_last_activated_by_fkey FOREIGN KEY (last_activated_by) REFERENCES users(id);

ALTER TABLE ONLY configurations_locks
    ADD CONSTRAINT configurations_locks_configuration_id_fkey FOREIGN KEY (configuration_id) REFERENCES configurations(id);

ALTER TABLE ONLY configurations_locks
    ADD CONSTRAINT configurations_locks_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE ONLY events
    ADD CONSTRAINT fk_configuration FOREIGN KEY (configuration_id) REFERENCES configurations(id);

ALTER TABLE ONLY events
    ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE ONLY sessions
    ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE ONLY users
    ADD CONSTRAINT users_jurisdiction_id_fkey FOREIGN KEY (jurisdiction_id) REFERENCES jurisdictions(id);

-- migrate:down
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS configurations_locks;
DROP TABLE IF EXISTS configurations;
DROP TABLE IF EXISTS conditions;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS jurisdictions;

DROP FUNCTION IF EXISTS configurations_set_condition_canonical_url_on_insert();
DROP FUNCTION IF EXISTS configurations_set_last_activated_at_on_status_change();
DROP FUNCTION IF EXISTS configurations_set_version_on_insert();
DROP FUNCTION IF EXISTS set_updated_at();

DROP TYPE IF EXISTS event_type_enum;
DROP TYPE IF EXISTS configuration_status;
