set working-directory := '../../'

docker := require("docker")

alias h := _default
alias help := _default
alias b := build-all
alias ba := build-app
alias bl := build-lambda
alias bo := build-ops

@_default:
    just --list docker

[doc("Build the application container locally")]
build-app:
    {{ docker }} build -t refiner-app -f Dockerfile.app .

[doc("Build the lambda container locally")]
build-lambda:
    {{ docker }} build -t refiner-lambda -f Dockerfile.lambda .

[doc("Build the ops container locally")]
build-ops:
    {{ docker }} build -t refiner-ops -f Dockerfile.ops .

[doc("Build all project containers locally")]
build-all: build-app build-lambda build-ops
