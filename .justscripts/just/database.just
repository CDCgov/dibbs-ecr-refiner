set working-directory := '../../refiner'
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
    just db query "SELECT t.version, COUNT(*) FROM conditions c JOIN tes t ON t.id = c.tes_id GROUP BY t.version ORDER BY t.version;"

[doc('Find a condition by its name (case-insensitive search)')]
[group('db')]
find-condition NAME:
    just db query "SELECT c.id, c.canonical_url, t.version, c.display_name FROM conditions c JOIN tes t ON t.id = c.tes_id WHERE c.display_name ILIKE '%{{ NAME }}%' ORDER BY c.display_name, t.version;"

[doc('Show the 5 most recently created configurations')]
[group('db')]
recent-configurations:
    just db query "SELECT id, version, jurisdiction_id, name FROM configurations ORDER BY created_at DESC LIMIT 5;"

[doc('Check if conditions exist for a specific version (e.g., `just db check-condition-version 3.0.0`)')]
[group('db')]
check-condition-version VERSION:
    just db query "SELECT t.version, c.display_name, c.canonical_url FROM conditions c JOIN tes t ON t.id = c.tes_id WHERE t.version = '{{ VERSION }}' LIMIT 5;"

[doc('Find all configurations for a specific jurisdiction (e.g., `just db check-configs-by-jurisdiction wa`)')]
[group('db')]
check-configs-by-jurisdiction JURISDICTION_ID:
    just db query "SELECT name, version, jurisdiction_id FROM configurations WHERE jurisdiction_id = '{{ JURISDICTION_ID }}';"

[doc('Find configurations for a jurisdiction and condition name (e.g., `just db check-config-combo wa zika`)')]
[group('db')]
check-config-combo JURISDICTION_ID CONDITION_NAME:
    just db query "SELECT c.name, c.jurisdiction_id, cond.display_name FROM configurations c JOIN configurations_conditions cc ON cc.configuration_id = c.id AND cc.is_primary JOIN conditions cond ON cond.id = cc.condition_id WHERE c.jurisdiction_id = '{{ JURISDICTION_ID }}' AND cond.display_name ILIKE '%{{ CONDITION_NAME }}%';"

[doc('Find a code within a condition and TES version. Usage: just db find-code "COVID-19" "7.0.0" "94500-6"')]
[group('db')]
find-code CONDITION VERSION CODE:
    just db query "SELECT c.display_name, t.version, s.display_name AS system, co.code, co.display, v.display_name AS grouper, cct.is_child_rsg, cct.is_trigger_code FROM conditions c JOIN tes t ON t.id = c.tes_id JOIN conditions_codes_temp cct ON cct.condition_id = c.id JOIN codes co ON co.id = cct.code_id JOIN systems s ON s.id = co.system_id JOIN valuesets v ON v.id = cct.valueset_id WHERE c.display_name = '{{ CONDITION }}' AND t.version = '{{ VERSION }}' AND co.code = '{{ CODE }}';"

[doc('Cascade delete all the related configuration artifacts. For use after an E2E test run')]
[group('db')]
delete-configuration CONFIGURATION_NAME:
    just db query "DELETE FROM configurations WHERE name = '{{ CONFIGURATION_NAME }}';"

[doc('Set the jurisdiction for the "refiner" user. Creates the jurisdiction record if it does not exist')]
[group('db')]
set-jd JURISDICTION_ID:
    just db query "\
        INSERT INTO jurisdictions (id, name, state_code) \
        VALUES ('{{ JURISDICTION_ID }}', '{{ JURISDICTION_ID }}', '{{ JURISDICTION_ID }}') \
        ON CONFLICT (id) DO NOTHING; \
        UPDATE users \
        SET jurisdiction_id = '{{ JURISDICTION_ID }}' \
        WHERE username = 'refiner';"
