set working-directory := '../../client'

alias h := _default
alias help := _default

@_default:
    just --list client

npm := require('npm')
npx := require('npx')

alias r := run

[doc('Run arbitrary `npm run *` commands within `client/`')]
[group('npm')]
run *ARGS:
    @test '{{ ARGS }}' == '' && {{ npm }} run || echo
    @for action in {{ ARGS }}; do {{ npm }} run $action; done

alias i := install

[doc('Run arbitrary `npm install *` commands within `client/')]
[group('dependencies')]
install *ARGS:
    {{ npm }} install {{ ARGS }}

alias t := test

[doc('Run arbitrary `npx playwright <command>` within `client/` (e.g. `just client playwright test`)')]
[group('e2e')]
playwright *ARGS:
    {{ npx }} playwright {{ ARGS }}

[doc('Run e2e Playwright tests in dev mode; use this for local/regression testing')]
[group('e2e')]
e2e:
    {{ npm }} run e2e:dev

[doc('Run ui/ux tests')]
[group('test')]
test:
    just client run test
