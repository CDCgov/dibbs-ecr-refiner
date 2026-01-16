set working-directory := '../..'

docker := require("docker")

@_default:
    just --list dev

alias u := up
alias d := down

[group('docker')]
[doc("Start only the project's core services with docker compose.")]
up *ARGS:
    {{ docker }} compose -f {{ absolute_path('./docker-compose.yaml') }} up {{ ARGS }}

[group('docker')]
[doc("Stop the project's core services with docker compose.")]
down *ARGS:
    {{ docker }} compose -f {{ absolute_path('./docker-compose.yaml') }} down -v {{ ARGS }}

[group('docker')]
[doc("Remove the project's core services and their volumes with docker compose.")]
rm:
    {{ docker }} compose -f {{ absolute_path('./docker-compose.yaml') }} rm -v
