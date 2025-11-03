# Data Migrations
These scripts are for one-off data migrations or backfills that should not be tracked by golang-migrate.

## How to run example
`psql $DATABASE_URL -f migrations/data_updates/2025-10-29_update_included_conditions.sql`

## Current Data Update Scripts
- **2025-10-29_update_included_conditions.sql**
    - Updates `configurations.included_conditions` to store condition IDs instead of canonical URLs and versions
    - Run manually after deploy.


