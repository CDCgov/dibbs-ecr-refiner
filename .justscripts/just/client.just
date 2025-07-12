set working-directory := '../../client'

alias h := _default
alias help := _default

@_default:
    just --list client

npm := require('npm')

alias r := run

[group('npm')]
[doc('Run arbitrary `npm run *` commands within `client/`')]
run *ARGS:
    @test '{{ ARGS }}' == '' && {{ npm }} run || echo
    @for action in {{ ARGS }}; do {{ npm }} run $action; done

alias i := install

[group('dependencies')]
[doc('Run arbitrary `npm install *` commands within `client/')]
install *ARGS:
    {{ npm }} install {{ ARGS }}

alias t := test

[group('test')]
[doc('Run ui/ux tests')]
test:
    just client run test
