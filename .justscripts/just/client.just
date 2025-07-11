set working-directory := '../../client'

alias h := _default
alias help := _default

@_default:
    just --list client

alias d := dev

[doc("Run abitrary `docker compose *` commands using project's docker-compose.yaml file.")]
dev +ARGS:
    docker compose -f {{ absolute_path('../docker-compose.yaml') }} {{ ARGS }}

alias r := run

[doc('Run arbitrary `npm run *` commands within `client/`')]
run *ARGS:
    @test  '{{ ARGS }}' == '' && npm run || echo
    @for action in {{ ARGS }}; do npm run $action; done
