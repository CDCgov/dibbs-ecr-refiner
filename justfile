alias h := _default
alias help := _default

@_default:
    just --list

[group('alias')]
[doc('Alias for `client`')]
mod c './.justscripts/just/client.just'

[group('sub-command')]
[doc('Run commands against `client/` code')]
mod client './.justscripts/just/client.just'

alias d := dev

docker := require("docker")

[group('docker')]
[doc("Run abitrary `docker compose *` commands using project's docker-compose.yaml file.")]
dev +ARGS:
    {{ docker }} compose -f {{ absolute_path('./docker-compose.yaml') }} {{ ARGS }}
