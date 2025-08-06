set dotenv-load

set working-directory := '../../refiner'

alias h := _default
alias help := _default

alias s := seed
alias c := check
alias q := query

@_default:
    just --list database

# Convinience paths to scripts
seed_db := absolute_path('scripts/seed_terminology_db.py')
check_db := absolute_path('scripts/check_terminology_db.py')
query_db := absolute_path('scripts/query_terminology_db.py')

# WARN: Required environment variables that we want to break execution on when
# using Just
DB_URL := env('DB_URL')
TES_API_URL := env('TES_API_URL')
TES_API_KEY := env('TES_API_KEY')

_venv:
    [ -d .venv ] || python3 -m venv .venv

[group('db')]
[doc('Seed the database with the terminology from TES')]
seed: _venv
    .venv/bin/python3 {{ seed_db }}

[group('db')]
[doc('Check the terminology in the database')]
check: _venv
    .venv/bin/python3 {{ check_db }}

[group('db')]
[doc('Query the terminology in the database')]
query: _venv
    .venv/bin/python3 {{ query_db }}

