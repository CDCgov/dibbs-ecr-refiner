# start from the official PostgreSQL 16 image
FROM postgres:16-alpine

# the working directory for our custom scripts and data
WORKDIR /app

# install python and pip for the seeding script
RUN apk add --no-cache python3 py3-pip

# setup and seeding
# * copy the single schema file. the entrypoint will run this first.
COPY ./schema/*.sql /docker-entrypoint-initdb.d/

# python script and its dependencies
COPY ./requirements.txt ./scripts/requirements.txt
COPY ./scripts/database_seeding.py ./scripts/database_seeding.py
COPY ./scripts/sample_configuration_seed_data.json ./scripts/sample_configuration_seed_data.json
RUN pip install --no-cache-dir --break-system-packages -r ./scripts/requirements.txt

# data for the seeder
COPY ./data /app/data

# the shell script to run the python seeder (runs last)
COPY ./scripts/run_seeding.sh /docker-entrypoint-initdb.d/99-run-seeding.sh

# no custom CMD is needed. The base image handles startup.
