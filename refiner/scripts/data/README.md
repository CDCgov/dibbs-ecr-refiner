# Data Directory

This directory contains all data used by the scripts in the parent `scripts/` directory. This includes source data, generated sample data, and configuration files for seeding the database.

The data is organized into the following subdirectories, with a distinction between foundational "source" data and derived or configuration-specific data.

## Directory Structure

### `source-ecr-files/`

**Purpose:** Holds the canonical, raw source for eICR (electronic Initial Case Report) and RR (Reportability Response) document pairs.

- This is the **single source of truth** for all eCR-related test data.
- Files in this directory are used for validation and as the basis for generating other, more specific test data sets.
- The CDA validation helpers now live in `refiner/tests/validation/`, and the eICR
  fixtures they run against moved with them to `refiner/tests/source-ecr-files/`.

### `source-tes-groupers/` — moved

**Moved to `refiner/tes/data/source-tes-groupers/`.**

The raw TES ValueSet bundles now live alongside the pipeline that fetches and processes
them. See `refiner/tes/README.md`.
- The `manifest.json` has a checksum that helps us track changes in these files over time.

Trigger codes no longer come from TES: they are fetched from the eRSD API into
`refiner/tes/data/source-ersd/`. They still only set `is_trigger_code` on codes the
groupers already supplied, never adding code rows of their own. See the `fetch/` section
of `refiner/tes/README.md`.

### `jurisdiction-packages/`

**Purpose:** Contains generated, jurisdiction-specific sample eCR files, packaged as `.zip` archives.

- The data in this directory is **derived from** the files in `source-ecr-files/`.
- The script `create_sample_data_by_jd.py` modifies the source files to create versions specific to each jurisdiction, making them ready for application testing.

### `sample-configurations/`

**Purpose:** Stores sample configuration data used for seeding the database.

- This data is used to populate the database with realistic configuration settings for a sample jurisdiction after the initial schema is seeded.
- This makes the application appear pre-configured and ready for use in a development or testing environment.
