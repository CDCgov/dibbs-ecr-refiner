alias h := _default
alias help := _default

@_default:
    just --list migrate

# ---------------------
# Database migrations
# ---------------------

[group('migrate')]
[doc('Run migrations with migrate for a given environment (local, demo, prod)')]
run ENV +ARGS='up':
    sh -c '../sh/get_db_url.sh {{ENV}} | xargs -I {} docker compose exec -T migrate migrate -path /app/refiner/migrations -database {} {{ARGS}}'


[group('migrate')]
[doc('Shortcut: migrate local')]
local +ARGS='up':
    just -f migrate.just run local {{ARGS}}

[group('migrate')]
[doc('Shortcut: migrate demo')]
demo +ARGS='up':
    just -f migrate.just run demo {{ARGS}}

[group('migrate')]
[doc('Shortcut: migrate prod')]
prod +ARGS='up':
    just -f migrate.just run prod {{ARGS}}

[group('migrate')]
[doc('Create a new migration script')]
create NAME:
    docker compose exec migrate migrate create -ext sql -dir /app/refiner/migrations -seq {{NAME}}
