alias h := _default
alias help := _default

@_default:
    just --list migrate

# ---------------------
# Database migrations
# ---------------------

[doc('Run migrations with migrate for a given environment (local, demo, prod)')]
[group('migrate')]
run ENV +ARGS='migrate':
    sh -c '../sh/get_db_url.sh {{ ENV }} | xargs -I {} docker compose exec -T migrate dbmate --migrations-dir /app/refiner/migrations --schema-file /app/refiner/schema.sql --url {} {{ ARGS }}'

[doc('Shortcut: migrate local')]
[group('migrate')]
local +ARGS='migrate':
    just -f migrate.just run local {{ ARGS }}

[doc('Create a new migration script')]
[group('migrate')]
create NAME:
    docker compose exec migrate dbmate --migrations-dir /app/refiner/migrations new {{ NAME }}
