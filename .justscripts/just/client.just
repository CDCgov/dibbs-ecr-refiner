set working-directory := '../../client'

alias h := _default
alias help := _default

@_default:
    just --list client

alias d := dev

[doc('Bring up development environment using Docker Compose')]
dev:
    docker-compose -f {{ absolute_path('../docker-compose.yaml') }} up

alias r := run

[doc('Run arbitrary `npm run *` commands within `client/`')]
run *ARGS:
    @test  '{{ ARGS }}' == '' && npm run || echo
    @for action in {{ ARGS }}; do npm run $action; done
