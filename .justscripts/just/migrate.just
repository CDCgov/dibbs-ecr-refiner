alias h := _default
alias help := _default

@_default:
    just --list migrate

# ---------------------
# Database migrations
# ---------------------

[group('migrate')]
[doc('Run migrations with migrate for a given environment (local, dev, prod)')]
run ENV +ARGS='up':
    docker compose run --rm migrate -path /app/refiner/migrations -database {{ shell('../../get_db_url.sh local') }} {{ ARGS }}


[group('migrate')]
[doc('Shortcut: migrate local')]
local +ARGS='up':
    just -f migrate.just migrate local {{ARGS}}

[group('migrate')]
[doc('Shortcut: migrate dev')]
dev +ARGS='up':
    just -f migrate.just migrate dev {{ARGS}}

[group('migrate')]
[doc('Shortcut: migrate prod')]
prod +ARGS='up':
    just -f migrate.just migrate prod {{ARGS}}

[group('migrate')]
[doc('Create a new migration script')]
create NAME:
    docker compose run --rm migrate create -ext sql -dir /app/refiner/migrations -seq {{NAME}}
