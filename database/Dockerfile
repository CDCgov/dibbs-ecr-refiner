# start from the official PostgreSQL 16 image
FROM postgres:16-alpine

# the working directory for our custom scripts and data
WORKDIR /app

# install python and pip for the seeding script
RUN apk add --no-cache python3 py3-pip

# setup and seeding
# * copy each .sql file individually
# * the numeric prefixes ensure they are executed in the correct order

# 1: schema
COPY ./schema/01-base-schema.sql /docker-entrypoint-initdb.d/10-base-schema.sql

# 2: functions
COPY ./functions/01-get-aggregated-child-codes.sql /docker-entrypoint-initdb.d/20-functions-aggregated-child-codes.sql
COPY ./functions/02-get-all-codes-from-grouper.sql /docker-entrypoint-initdb.d/21-functions-get-all-codes.sql

# 3: triggers
COPY ./triggers/01-aggregate-base-groupers.sql /docker-entrypoint-initdb.d/30-triggers-aggregate-base-groupers.sql
COPY ./triggers/02-update-refinement-cache.sql /docker-entrypoint-initdb.d/31-triggers-update-refinement-cache.sql

# 4: python script and its dependencies
COPY ./requirements.txt ./scripts/requirements.txt
COPY ./scripts/database_seeding.py ./scripts/database_seeding.py
RUN pip install --no-cache-dir --break-system-packages -r ./scripts/requirements.txt

# 5: data for the seeder
COPY ./data /app/data

# 6: the shell script to run the python seeder (runs last)
COPY ./scripts/run_seeding.sh /docker-entrypoint-initdb.d/99-run-seeding.sh

# no custom CMD is needed. The base image handles startup.
