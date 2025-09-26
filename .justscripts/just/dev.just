set working-directory := '../..'

dev_services_list := "migrate client refiner-service db auth localstack"
docker := require("docker")

alias u := up
alias d := down

[group('docker')]
[doc("Start only the project's core services with docker compose.")]
up *ARGS:
    {{ docker }} compose -f {{ absolute_path('./docker-compose.yaml') }} up {{ ARGS }} {{ dev_services_list }}

[group('docker')]
[doc("Stop the project's core services with docker compose.")]
down:
    {{ docker }} compose -f {{ absolute_path('./docker-compose.yaml') }} down {{ dev_services_list }}

[group('docker')]
[doc("Remove the project's core services and their volumes with docker compose.")]
rm:
    {{ docker }} compose -f {{ absolute_path('./docker-compose.yaml') }} rm -v {{ dev_services_list }}
