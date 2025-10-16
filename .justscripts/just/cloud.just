alias h := _default
alias help := _default

@_default:
    just --list cloud

[doc('Retrieve the DB_URL for the Demo environment')]
[group('azure')]
demo-db-url:
    az container show \
    --name dibbs-er-demo-aci \
    --resource-group dibbs-er-demo \
    --query "containers[0].environmentVariables[?name=='DB_URL'].value | [0]" \
    -o tsv
