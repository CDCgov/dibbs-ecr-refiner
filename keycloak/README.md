# Keycloak

This directory contains files related to [Keycloak](https://www.keycloak.org/) which is used by the Refiner for identity and access management in development.

## Refiner Realm

`refiner-realm.json` defines the "realm" that is configured to work with the Refiner application.

It's important to note that making changes in the Keycloak GUI will not automatically update this file. If you make changes in the GUI and want them to persist, you can run the `./update-realm.sh` script. This script can be run while the Keycloak dev server is up and running.
