set working-directory := '../../refiner'

alias h := _default
alias help := _default

@_default:
    just --list server


# Convinience paths to scripts
seed_terminology_db := absolute_path('scripts/seed_terminology_db.py')
check_terminology_db := absolute_path('scripts/check_terminology_db.py')
query_terminology_db := absolute_path('scripts/query_terminology_db.py')

# WARN: Required environment variables that we want to break execution on when
# using Just
DB_URL := env('DB_URL')
TES_API_URL := env('TES_API_URL')
TES_API_KEY := env('TES_API_KEY')

[group('db')]
[doc('Seed the database with the terminology from TES')]
seed-db:
    python {{ seed_terminology_db }}

[group('db')]
[doc('Check the terminology in the database')]
check-db:
    python {{ check_terminology_db }}

[group('db')]
[doc('Query the terminology in the database')]
query-db:
    python {{ query_terminology_db }}
