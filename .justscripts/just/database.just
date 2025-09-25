set working-directory := '../../refiner/scripts'

set dotenv-load

alias h := _default
alias help := _default

alias c := clean

@_default:
    just --list database

[group('db')]
[doc('Completely wipes the refiner local development database')]
clean:
    docker compose exec db psql -U postgres -d refiner -f drop-all.sql

[group('db')]
[doc('Runs the seeding script to seed the database with condition data')]
seed:
    docker compose run --rm seed

[group('db')]
[doc('Runs a full database refresh (wipe, migrate, seed)')]
refresh:
    just db clean && just migrate local && just db seed

[group('db')]
[doc('Run all DB sanity checks (seeding, integrity, etc)')]
check_seeding:
    python maintenance/check_seeded_db.py

[group('db')]
[doc('Run a raw SQL query against the database (e.g., `just db query "SELECT * FROM conditions LIMIT 5;"`)')]
query +QUERY:
    docker compose exec db psql -U postgres -d refiner -c "{{QUERY}}"

[group('db')]
[doc('List all tables in the public schema')]
tables:
    just db query "\dt"

[group('db')]
[doc('Describe the schema of a table (e.g., `just db table conditions`)')]
table TABLE:
    just db query "\d {{TABLE}}"

[group('db')]
[doc('Get the count of conditions, grouped by version')]
count-conditions:
    just db query "SELECT version, COUNT(*) FROM conditions GROUP BY version ORDER BY version;"

[group('db')]
[doc('Find a condition by its name (case-insensitive search)')]
find-condition NAME:
    just db query "SELECT id, canonical_url, version, display_name FROM conditions WHERE display_name ILIKE '%{{NAME}}%';"

[group('db')]
[doc('Show the 5 most recently created configurations')]
recent-configurations:
    just db query "SELECT id, version, jurisdiction_id, name FROM configurations ORDER BY created_at DESC LIMIT 5;"

[group('db')]
[doc('Check if conditions exist for a specific version (e.g., `just db check-condition-version 3.0.0`)')]
check-condition-version VERSION:
    just db query "SELECT version, display_name, canonical_url FROM conditions WHERE version = '{{VERSION}}' LIMIT 5;"

[group('db')]
[doc('Find all configurations for a specific jurisdiction (e.g., `just db check-configs-by-jurisdiction wa`)')]
check-configs-by-jurisdiction JURISDICTION_ID:
    just db query "SELECT name, version, jurisdiction_id FROM configurations WHERE jurisdiction_id = '{{JURISDICTION_ID}}';"

[group('db')]
[doc('Find configurations for a jurisdiction and condition name (e.g., `just db check-config-combo wa zika`)')]
check-config-combo JURISDICTION_ID CONDITION_NAME:
    just db query "SELECT c.name, c.jurisdiction_id, cond.display_name FROM configurations c JOIN conditions cond ON c.condition_id = cond.id WHERE c.jurisdiction_id = '{{JURISDICTION_ID}}' AND cond.display_name ILIKE '%{{CONDITION_NAME}}%';"
