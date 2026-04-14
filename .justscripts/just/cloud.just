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

[doc('Retrieve a list of jurisdictions who have authored conditions in the demo application')]
[group('azure')]
demo-jurisdiction-authored:
    psql $(just cloud demo-db-url) -c "SELECT c.jurisdiction_id, c.name FROM configurations AS c ORDER BY c.jurisdiction_id;"
