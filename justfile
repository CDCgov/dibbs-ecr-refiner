alias h := _default
alias help := _default

@_default:
    just --list --list-submodules

[group('alias')]
[doc('Alias for `client`')]
mod c './.justscripts/just/client.just'

[group('alias')]
[doc('Alias for `database`')]
mod db './.justscripts/just/database.just'

[group('alias')]
[doc('Alias for `migrate`')]
mod m './.justscripts/just/migrate.just'

[group('alias')]
[doc('Alias for `server`')]
mod s './.justscripts/just/server.just'

[group('sub-command')]
[doc('Run commands against `client/` code')]
mod client './.justscripts/just/client.just'

[group('alias')]
[doc('Alias for `dev`')]
mod d './.justscripts/just/dev.just'

[group('sub-command')]
[doc('Run dev-related docker compose commands')]
mod dev './.justscripts/just/dev.just'

[group('sub-command')]
[doc('Run database commands against `refiner/` code')]
mod database './.justscripts/just/database.just'

[group('sub-command')]
[doc('Run migration commands')]
mod migrate './.justscripts/just/migrate.just'

[group('sub-command')]
[doc('Run server commands against `refiner/` code')]
mod server './.justscripts/just/server.just'

alias l := lint
alias t := test

[doc('Run linting and formatting rules on all code')]
lint:
    just client::run lint fmt
    just server::lint

[group('test')]
[doc('Run tests on all code')]
test:
    just server::test
    just client::run test:coverage
    just client::run e2e

az := require("az")

[doc('Retrieve the DB_URL for the Demo environment')]
[group('azure')]
demo-db-url:
    {{ az }} container show \
      --name dibbs-er-demo-aci \
      --resource-group dibbs-er-demo \
      --query "containers[0].environmentVariables[?name=='DB_URL']" \
      -o table
