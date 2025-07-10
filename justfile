alias h := _default
alias help := _default

@_default:
    just --list


[doc('Alias for `client`')]
mod c './.justscripts/just/client.just'

[doc('Run commands against `client/` code')]
mod client './.justscripts/just/client.just'
