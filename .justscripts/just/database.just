set working-directory := '../../refiner/scripts'
set dotenv-load := true

alias h := _default
alias help := _default
alias c := clean

@_default:
    just --list database

[doc('Completely wipes the refiner local development database')]
[group('db')]
clean:
    docker compose exec db psql -U postgres -d refiner -f drop-all.sql

[doc('Runs the seeding script to seed the database with condition data')]
[group('db')]
seed:
    docker compose run --rm seed

[doc('Runs a full database refresh (wipe, migrate, seed)')]
[group('db')]
refresh:
    just db clean && just migrate local && just db seed

[doc('Run all DB sanity checks (seeding, integrity, etc)')]
[group('db')]
check_seeding:
    python maintenance/check_seeded_db.py

[doc('Run a raw SQL query against the database (e.g., `just db query "SELECT * FROM conditions LIMIT 5;"`)')]
[group('db')]
query +QUERY:
    docker compose exec db psql -U postgres -d refiner -c "{{ QUERY }}"

[doc('List all tables in the public schema')]
[group('db')]
tables:
    just db query "\dt"

[doc('Describe the schema of a table (e.g., `just db table conditions`)')]
[group('db')]
table TABLE:
    just db query "\d {{ TABLE }}"

[doc('Get the count of conditions, grouped by version')]
[group('db')]
count-conditions:
    just db query "SELECT version, COUNT(*) FROM conditions GROUP BY version ORDER BY version;"

[doc('Find a condition by its name (case-insensitive search)')]
[group('db')]
find-condition NAME:
    just db query "SELECT id, canonical_url, version, display_name FROM conditions WHERE display_name ILIKE '%{{ NAME }}%';"

[doc('Show the 5 most recently created configurations')]
[group('db')]
recent-configurations:
    just db query "SELECT id, version, jurisdiction_id, name FROM configurations ORDER BY created_at DESC LIMIT 5;"

[doc('Check if conditions exist for a specific version (e.g., `just db check-condition-version 3.0.0`)')]
[group('db')]
check-condition-version VERSION:
    just db query "SELECT version, display_name, canonical_url FROM conditions WHERE version = '{{ VERSION }}' LIMIT 5;"

[doc('Find all configurations for a specific jurisdiction (e.g., `just db check-configs-by-jurisdiction wa`)')]
[group('db')]
check-configs-by-jurisdiction JURISDICTION_ID:
    just db query "SELECT name, version, jurisdiction_id FROM configurations WHERE jurisdiction_id = '{{ JURISDICTION_ID }}';"

[doc('Find configurations for a jurisdiction and condition name (e.g., `just db check-config-combo wa zika`)')]
[group('db')]
check-config-combo JURISDICTION_ID CONDITION_NAME:
    just db query "SELECT c.name, c.jurisdiction_id, cond.display_name FROM configurations c JOIN conditions cond ON c.condition_id = cond.id WHERE c.jurisdiction_id = '{{ JURISDICTION_ID }}' AND cond.display_name ILIKE '%{{ CONDITION_NAME }}%';"
