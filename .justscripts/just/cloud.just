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

[doc('Retrieve the current backend address pool configuration for the Demo environment')]
[group('azure')]
demo-show-network-address-pool:
    az network application-gateway address-pool show \
      --subscription 6848426c-8ca8-4832-b493-fed851be1f95 \
      --resource-group dibbs-global-demo \
      --gateway-name hub-appgw \
      --name dibbs-global-demo-be-ecr-refiner

[doc('Update the current backend address pool configuration for the Demo environment')]
[group('azure')]
demo-update-network-address-pool ip_or_fqdn:
    az network application-gateway address-pool update \
      --subscription 6848426c-8ca8-4832-b493-fed851be1f95 \
      --resource-group dibbs-global-demo \
      --gateway-name hub-appgw --name \
      --name dibbs-global-demo-be-ecr-refiner \
      --servers {{ ip_or_fqdn }}
