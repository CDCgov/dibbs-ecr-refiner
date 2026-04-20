set working-directory := '../..'

docker := require("docker")
compose_files := "-f " + absolute_path('./docker-compose.yml') + " -f " + absolute_path('./docker-compose.override.yml')

@_default:
    just --list dev

alias u := up
alias d := down

[doc("Start only the project's core services with docker compose.")]
[group('docker')]
up *ARGS:
    {{ docker }} compose up {{ ARGS }}

[doc("Stop the project's core services with docker compose.")]
[group('docker')]
down *ARGS:
    {{ docker }} compose {{ compose_files }} down -v {{ ARGS }}

[doc("Remove the project's core services and their volumes with docker compose.")]
[group('docker')]
rm:
    {{ docker }} compose {{ compose_files }} rm -v

show_tbl := 'table {{.Names}}\t{{.Ports}}\t{{.ID}}'

[doc('Show running `dibbs-ecr-refiner` containers with helpful output')]
[group('docker')]
show:
    {{ docker }} container ls --filter 'name=dibbs-ecr-refiner' --format "{{ show_tbl }}"
