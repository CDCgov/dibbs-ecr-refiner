# Build client
FROM node:20-alpine3.20 AS client-builder

WORKDIR /src

COPY ./client/package*.json ./
RUN npm install

COPY ./client ./

RUN npm run build

# Package production app
FROM python:3.13-slim

RUN apt-get update && \
    apt-get upgrade -y

RUN pip install --upgrade pip  --break-system-packages

WORKDIR /code

COPY ./refiner/requirements.txt /code/requirements.txt
RUN pip install -r requirements.txt

COPY ./refiner/app /code/app
COPY ./refiner/assets /code/assets
COPY ./refiner/README.md /code/README.md
COPY --from=client-builder /src/dist /code/dist

ENV PRODUCTION=true

EXPOSE 8080
CMD uvicorn app.main:app --host 0.0.0.0 --port 8080
