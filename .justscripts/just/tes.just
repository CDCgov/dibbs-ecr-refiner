set working-directory := '../../refiner'
set dotenv-load := true

alias h := _default
alias help := _default
alias f := fetch
alias n := normalize
alias v := verify
alias vp := verify-processed
alias vd := verify-db

@_default:
    just --list tes

[doc('Fetch grouper data from the TES API into data/source-tes-groupers (needs TES_API_KEY in your .env)')]
[group('tes')]
fetch:
    docker compose exec server python -m tes.fetch.detect_changes

[doc('Check that newly fetched bundles still parse the way the seeding pipeline expects')]
[group('tes')]
verify-bundles:
    docker compose exec server python -m tes.verify.validate_tes_valuesets

[doc('Check data/processed is intact, current, and exactly what normalize produces')]
[group('tes')]
verify-processed *ARGS:
    docker compose exec server python -m tes.verify.processed {{ ARGS }}

[doc('Check the seeded database matches data/processed (safe against a live database)')]
[group('tes')]
verify-db:
    docker compose exec server python -m tes.verify.database

[doc('Run every verification: bundles, processed data, and the seeded database')]
[group('tes')]
verify:
    just tes verify-bundles && just tes verify-processed && just tes verify-db

[doc('Turn the raw FHIR bundles into the flat tables in data/processed that seeding reads')]
[group('tes')]
normalize:
    docker compose exec server python -m tes.normalize.run

[doc('Full per-release workflow: fetch from the API, verify, then rebuild data/processed')]
[group('tes')]
release:
    just tes fetch && just tes verify-bundles && just tes normalize && just tes verify-processed

[doc('Show what changed in data/processed since the last commit (per-grouper code counts)')]
[group('tes')]
diff:
    git diff --stat -- tes/data/processed/ && git diff -- tes/data/processed/summary.csv
