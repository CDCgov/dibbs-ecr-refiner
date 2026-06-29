alias h := _default
alias help := _default

@_default:
    just --list --list-submodules

# Alias for `docker`
[group: 'alias']
mod dk './.justscripts/just/docker.just'

# Alias for `client`
[group: 'alias']
mod c './.justscripts/just/client.just'

# Alias for `database`
[group: 'alias']
mod db './.justscripts/just/database.just'

# Alias for `risk-assessments`
[group: 'alias']
mod cve './.justscripts/just/risk-assessments.just'

# Alias for `decisions`
[group: 'alias']
mod rfc './.justscripts/just/decisions.just'

# Alias for `migrate`
[group: 'alias']
mod m './.justscripts/just/migrate.just'

# Alias for `server`
[group: 'alias']
mod s './.justscripts/just/server.just'

# Alias for `cloud`
[group: 'alias']
mod cd './.justscripts/just/cloud.just'

# Alias for `dev`
[group: 'alias']
mod d './.justscripts/just/dev.just'

# Run docker build commands
[group: 'sub-command']
mod docker './.justscripts/just/docker.just'

# Run commands against `client/` code
[group: 'sub-command']
mod client './.justscripts/just/client.just'

# Run dev-related docker compose commands
[group: 'sub-command']
mod dev './.justscripts/just/dev.just'

# Run database commands against `refiner/` code
[group: 'sub-command']
mod database './.justscripts/just/database.just'

# Run migration commands
[group: 'sub-command']
mod migrate './.justscripts/just/migrate.just'

# Run server commands against `refiner/` code
[group: 'sub-command']
mod server './.justscripts/just/server.just'

# Run commands against Azure
[group: 'sub-command']
mod cloud './.justscripts/just/cloud.just'

# Run risk assessments commands
[group: 'sub-command']
mod risk-assessments './.justscripts/just/risk-assessments.just'

# Run decision records commands
[group: 'sub-command']
mod decisions './.justscripts/just/decisions.just'

alias l := lint
alias t := test

[doc('Run linting and formatting rules on all code')]
lint:
    just client::run lint fmt
    just server::lint

[doc('Run tests on all code')]
[group('test')]
test:
    just server::test
    just client::run test:coverage
    just client::run e2e

# NOTE: The recipe below named `_new` is **only** called from other Justfiles
# that create files from .template files found in certain directories.
# Currently it's used for managing and authoring `docs/decisions` and
# `docs/risk-assessments`

[private]
_new title type folder:
    #!/usr/bin/env deno --allow-env --allow-write --allow-read
    const JUST_TITLE = "{{ title }}"
    const JUST_TITLE_SAFE = "{{ kebabcase(title) }}"
    const JUST_TYPE = "{{ type }}"
    const JUST_FOLDER = "{{ folder }}"
    const JUST_RUN_DIR = "{{ replace(justfile_directory(), '\', '/') }}"
    {{ read('./.justscripts/ts/new-file.ts') }}
