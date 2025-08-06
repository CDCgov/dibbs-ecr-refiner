# Keycloak

This directory contains files related to [Keycloak](https://www.keycloak.org/) which is used by the Refiner for identity and access management in development.

## Docker Compose

This directory contains a `docker-compose.yaml` file specifically for modifying our development Keycloak configuration. Unfortunately we need a dedicated database hooked up to Keycloak in order to run the export command, which is why this separate `docker-compose.yaml` file exists.

When an update command is run `exports/refiner-realm.json` is modified and will be imported by the Refiner's development main Docker Compose setup. That setup does not need its own dedicated Keycloak database.

### How to update the realm file

1. Shut down all of your running containers
2. Run the docker compose file in this directory - `docker compose up`
3. Load up [http://localhost:8080](http://localhost:8080) in your browser
4. Log in using `admin` as the username and `admin` as the password
5. Make your config changes using the GUI
6. When you're done making your changes you need to exec into the Keycloak container (`docker exec -it <container_id_or_name> /bin/bash`) and run the following command:

```sh
/opt/keycloak/bin/kc.sh export --dir=/opt/keycloak/data/export --realm=refiner --users=realm_file
```

Once run, your newly exported `refiner-realm.json` will be placed into `./exports` on your host machine (thanks to the volume we have defined).

## Developer Information

### Accessing the Keycloak GUI

1. With your containers running, navigate to [http://localhost:8082](http://localhost:8082)
2. Login using `admin` for the username and `admin` for the password
3. Select `refiner` as your realm (if not already selected)

### Test User

A test user has been created that developers can use to log into the Refiner app:

- username: `refiner`
- password: `refiner`

If you want to try logging into Keycloak directly (not through Refiner), the user login portal is here: [http://localhost:8082/realms/refiner/account](http://localhost:8082/realms/refiner/account).
