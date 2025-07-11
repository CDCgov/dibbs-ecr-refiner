set working-directory := '../../client'

alias h := _default
alias help := _default

@_default:
    just --list client

alias r := run

[group('npm')]
[doc('Run arbitrary `npm run *` commands within `client/`')]
run *ARGS:
    @test  '{{ ARGS }}' == '' && npm run || echo
    @for action in {{ ARGS }}; do npm run $action; done
