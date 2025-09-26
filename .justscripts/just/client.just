set working-directory := '../../client'

alias h := _default
alias help := _default

@_default:
    just --list client

npm := require('npm')
npx := require('npx')

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

[group('e2e')]
[doc('Run arbitrary `npx playwright <command>` within `client/` (e.g. `just client playwright test`)')]
playwright *ARGS:
    {{ npx }} playwright {{ ARGS }}

[group('e2e')]
[doc('Run e2e Playwright tests in dev mode; use this for local/regression testing')]
e2e:
    {{ npm }} run e2e:dev

[group('test')]
[doc('Run ui/ux tests')]
test:
    just client run test
