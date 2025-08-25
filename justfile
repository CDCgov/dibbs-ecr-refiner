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

[group('sub-command')]
[doc('Run database commands against `refiner/` code')]
mod database './.justscripts/just/database.just'

[group('sub-command')]
[doc('Run migration commands')]
mod migrate './.justscripts/just/migrate.just'

[group('sub-command')]
[doc('Run server commands against `refiner/` code')]
mod server './.justscripts/just/server.just'

alias d := dev

docker := require("docker")

[group('docker')]
[doc("Run abitrary `docker compose *` commands using project's docker-compose.yaml file.")]
dev +ARGS:
    {{ docker }} compose -f {{ absolute_path('./docker-compose.yaml') }} {{ ARGS }}

[doc('Run linting and formatting rules on all code')]
lint:
    just client::run lint fmt
    just server::lint

[group('test')]
[doc('Run tests on all code')]
test:
    just server::test
    just client::run test:coverage
