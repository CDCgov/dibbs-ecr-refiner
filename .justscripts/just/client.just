alias h := _default
alias help := _default

alias d := dev
alias r := run

@_default:
    just --list client

set working-directory := '../../client'

[doc('Bring up development environment using Docker Compose')]
dev:
    docker-compose -f '../../docker-compose.yaml' up


[doc('Run arbitrary `npm run *` commands within `client/`')]
run *ARGS:
    @test  '{{ ARGS }}' == '' && npm run || echo
    @for action in {{ ARGS }}; do npm run $action; done
