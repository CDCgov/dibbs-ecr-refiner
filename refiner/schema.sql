\restrict dbmate

-- Dumped from database version 18.2
-- Dumped by pg_dump version 18.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS '';


--
-- Name: configuration_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.configuration_status AS ENUM (
    'active',
    'inactive',
    'draft'
);


--
-- Name: event_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.event_type_enum AS ENUM (
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


--
-- Name: configurations_set_condition_canonical_url_on_insert(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.configurations_set_condition_canonical_url_on_insert() RETURNS trigger
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


--
-- Name: configurations_set_last_activated_at_on_status_change(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.configurations_set_last_activated_at_on_status_change() RETURNS trigger
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


--
-- Name: configurations_set_version_on_insert(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.configurations_set_version_on_insert() RETURNS trigger
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


--
-- Name: set_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: conditions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conditions (
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
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: configurations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.configurations (
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
    status public.configuration_status DEFAULT 'draft'::public.configuration_status NOT NULL,
    last_activated_at timestamp with time zone,
    last_activated_by uuid,
    condition_canonical_url text NOT NULL,
    created_by uuid NOT NULL,
    s3_urls text[],
    CONSTRAINT section_processing_must_be_json_array CHECK ((jsonb_typeof(section_processing) = 'array'::text))
);


--
-- Name: configurations_locks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.configurations_locks (
    configuration_id uuid NOT NULL,
    user_id uuid NOT NULL,
    expires_at timestamp without time zone NOT NULL
);


--
-- Name: events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    jurisdiction_id text NOT NULL,
    user_id uuid NOT NULL,
    configuration_id uuid NOT NULL,
    event_type public.event_type_enum NOT NULL,
    action_text text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: jurisdictions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.jurisdictions (
    id text NOT NULL,
    name text NOT NULL,
    state_code text
);


--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_migrations (
    version character varying NOT NULL
);


--
-- Name: sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sessions (
    token_hash text NOT NULL,
    user_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    username text NOT NULL,
    email text NOT NULL,
    jurisdiction_id text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: conditions conditions_canonical_url_version_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conditions
    ADD CONSTRAINT conditions_canonical_url_version_key UNIQUE (canonical_url, version);


--
-- Name: conditions conditions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conditions
    ADD CONSTRAINT conditions_pkey PRIMARY KEY (id);


--
-- Name: configurations configurations_condition_canonical_url_jurisdiction_id_vers_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configurations
    ADD CONSTRAINT configurations_condition_canonical_url_jurisdiction_id_vers_key UNIQUE (condition_canonical_url, jurisdiction_id, version);


--
-- Name: configurations_locks configurations_locks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configurations_locks
    ADD CONSTRAINT configurations_locks_pkey PRIMARY KEY (configuration_id);


--
-- Name: configurations configurations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configurations
    ADD CONSTRAINT configurations_pkey PRIMARY KEY (id);


--
-- Name: events events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (id);


--
-- Name: jurisdictions jurisdictions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.jurisdictions
    ADD CONSTRAINT jurisdictions_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (token_hash);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: configurations_one_active_per_pair_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX configurations_one_active_per_pair_idx ON public.configurations USING btree (condition_canonical_url, jurisdiction_id) WHERE (status = 'active'::public.configuration_status);


--
-- Name: configurations_one_draft_per_pair_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX configurations_one_draft_per_pair_idx ON public.configurations USING btree (condition_canonical_url, jurisdiction_id) WHERE (status = 'draft'::public.configuration_status);


--
-- Name: idx_conditions_child_snomed_codes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conditions_child_snomed_codes ON public.conditions USING gin (child_rsg_snomed_codes);


--
-- Name: configurations configurations_set_condition_canonical_url_trigger; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER configurations_set_condition_canonical_url_trigger BEFORE INSERT OR UPDATE OF condition_id ON public.configurations FOR EACH ROW EXECUTE FUNCTION public.configurations_set_condition_canonical_url_on_insert();


--
-- Name: configurations configurations_set_last_activated_at_on_status_change_trigger; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER configurations_set_last_activated_at_on_status_change_trigger BEFORE UPDATE OF status ON public.configurations FOR EACH ROW EXECUTE FUNCTION public.configurations_set_last_activated_at_on_status_change();


--
-- Name: configurations configurations_set_version_on_insert_trigger; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER configurations_set_version_on_insert_trigger BEFORE INSERT ON public.configurations FOR EACH ROW EXECUTE FUNCTION public.configurations_set_version_on_insert();


--
-- Name: conditions update_conditions_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_conditions_updated_at BEFORE UPDATE ON public.conditions FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: configurations update_configurations_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_configurations_updated_at BEFORE UPDATE ON public.configurations FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: users update_users_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: configurations configurations_condition_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configurations
    ADD CONSTRAINT configurations_condition_id_fkey FOREIGN KEY (condition_id) REFERENCES public.conditions(id);


--
-- Name: configurations configurations_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configurations
    ADD CONSTRAINT configurations_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: configurations configurations_jurisdiction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configurations
    ADD CONSTRAINT configurations_jurisdiction_id_fkey FOREIGN KEY (jurisdiction_id) REFERENCES public.jurisdictions(id);


--
-- Name: configurations configurations_last_activated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configurations
    ADD CONSTRAINT configurations_last_activated_by_fkey FOREIGN KEY (last_activated_by) REFERENCES public.users(id);


--
-- Name: configurations_locks configurations_locks_configuration_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configurations_locks
    ADD CONSTRAINT configurations_locks_configuration_id_fkey FOREIGN KEY (configuration_id) REFERENCES public.configurations(id);


--
-- Name: configurations_locks configurations_locks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configurations_locks
    ADD CONSTRAINT configurations_locks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: events fk_configuration; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT fk_configuration FOREIGN KEY (configuration_id) REFERENCES public.configurations(id);


--
-- Name: events fk_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: sessions sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: users users_jurisdiction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_jurisdiction_id_fkey FOREIGN KEY (jurisdiction_id) REFERENCES public.jurisdictions(id);


--
-- PostgreSQL database dump complete
--

\unrestrict dbmate


--
-- Dbmate schema migrations
--

INSERT INTO public.schema_migrations (version) VALUES
    ('20260226212322');
