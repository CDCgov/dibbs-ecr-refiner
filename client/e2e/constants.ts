/**
 * TES versions seeded into the local database.
 *
 * Local/CI seeding keeps only the two most recent releases (see
 * `collect_files_to_parse` in `refiner/scripts/seeding/lib/index.py`), so these
 * are the only versions any test can reference. Bump both when new TES data
 * lands, alongside `DEFAULT_TES_VERSION`/`PREV_TES_VERSION` in
 * `refiner/tests/integration/conftest.py`.
 */
export const LATEST_TES_VERSION = '7.0.0';
export const PREVIOUS_TES_VERSION = '6.0.0';
