# Build client
FROM node:22-alpine3.22 AS client-builder

WORKDIR /src

COPY ./client/package*.json ./
RUN npm ci

# Used as part of the client build
ARG VITE_GIT_HASH
ARG VITE_GIT_BRANCH
ENV VITE_GIT_HASH=$VITE_GIT_HASH
ENV VITE_GIT_BRANCH=$VITE_GIT_BRANCH

COPY ./client ./
RUN npm run build


# Runtime image
FROM python:3.14-slim

# default VERSION is 0.0.0 if not passed at build time
ARG VERSION="0.0.0"

# make it available as an environment variable inside the container
ENV VERSION=$VERSION

WORKDIR /code

RUN python -m pip install --upgrade pip

COPY ./refiner/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./refiner/app ./app
COPY ./refiner/assets ./assets
COPY ./refiner/README.md ./README.md
COPY --from=client-builder /src/dist ./dist

EXPOSE 8080
CMD ["uvicorn", "app.asgi:app", "--host", "0.0.0.0", "--port", "8080"]
