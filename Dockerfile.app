# Build client
FROM node:26-alpine3.23 AS client-builder

WORKDIR /src

COPY ./client/package*.json ./
RUN npm ci

# Used as part of the client build
ARG VITE_GIT_HASH
ARG VITE_GIT_BRANCH
ARG VERSION
ENV VITE_GIT_HASH=$VITE_GIT_HASH
ENV VITE_GIT_BRANCH=$VITE_GIT_BRANCH
ENV VITE_APP_VERSION=$VERSION

COPY ./client ./
RUN npm run build

# Install system deps
FROM python:3.14-alpine AS system-builder

RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    libxml2-dev \
    libxslt-dev

# build the lxml wheel
WORKDIR /app
RUN pip wheel --no-cache-dir --wheel-dir=/app/wheels lxml


# Runtime image
FROM python:3.14-alpine

# Pick up Alpine fixes the base image may lag on, including ca-certificates
# 20261020-r0, which drops the distrusted emSign ECC Root CA - G3.
RUN apk upgrade --no-cache

# install runtime C libs
RUN apk add --no-cache \
    libxml2 \
    libxslt

# default VERSION is 0.0.0 if not passed at build time
ARG VERSION="0.0.0"

# make it available as an environment variable inside the container
ENV VERSION=$VERSION

WORKDIR /code

RUN python -m pip install --upgrade pip

# copy & install wheel from builder
COPY --from=system-builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/*


COPY ./refiner/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./refiner/app ./app
COPY ./refiner/assets ./assets
COPY ./refiner/README.md ./README.md
COPY --from=client-builder /src/dist ./dist

# Fail the build if either distrusted root is left in any CA bundle, whether from
# the OS or vendored by a Python package. Each pattern is one line of a root's
# base64 body (emSign ECC Root CA - G3, then AAA Certificate Services), so it
# matches however a bundle labels the certificate. grep exits 1 only when
# nothing matched.
RUN grep -rlF \
    -e 'CUfvO6wIBHxcmbHtRwfSAjEAnbpV/KlK6O3t5nYBQnvI+GDZjVGLVTv7jHvrZQnD' \
    -e 'l2D4kF501KKaU73yqWjgom7C12yxow+ev+to51byrvLjKzg6CYG1a4XXvi3tPxq3' \
    /etc /usr /var; \
    test $? -eq 1

EXPOSE 8080
CMD ["uvicorn", "app.asgi:app", "--host", "0.0.0.0", "--port", "8080"]
