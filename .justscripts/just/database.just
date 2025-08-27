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
