# Getting Started with the DIBBs Message Refiner Service

## Introduction

The DIBBs Message Refiner service offers a REST API to pare down an incoming message to only the user-specified elements.

## Running the Message Refiner

You can run the Message Refiner run using Docker, any other OCI container runtime (e.g., Podman), or directly from the Python source code.

### Running with Docker (Recommended)

To run the Message Refiner with Docker, follow these steps.

1. Confirm that you have Docker installed by running `docker -v`. If you don't see a response similar to what's shown below, follow [these instructions](https://docs.docker.com/get-docker/) to install Docker.

2. Download a copy of the Docker image from the repository by running `docker pull ghcr.io/cdcgov/dibbs-ecr-refiner:latest`

3. Run the service with `docker run -p 8080:8080 dibbs-ecr-refiner:latest`.

Congratulations, the Message Refiner should now be running on `localhost:8080`!

### Running from Python Source Code

We recommend running the Message Refiner from a container, but if that isn't feasible for a given use -case, you can also run the service directly from Python using the steps below.

1. Ensure that both Git and Python 3.13 or higher are installed.
2. Clone the repository with `git clone https://github.com/CDCgov/dibbs-ecr-refiner`.
3. Navigate to the top-level directory of this repository.
4. Make a fresh virtual environment with `python -m venv .venv`.
5. Activate the virtual environment with `source .venv/bin/activate` (MacOS and Linux), `venv\Scripts\activate` (Windows Command Prompt), or `.venv\Scripts\Activate.ps1` (Windows Power Shell).
6. Install all of the Python dependencies for the Message Refiner with `pip install -r requirements.txt` into your virtual environment.
7. Run the Message Refiner on `localhost:8080` with `python -m uvicorn app.main:app --host 0.0.0.0 --port 8080`.

## Building the Docker Image

To build the Docker image for the Message Refiner from source instead of downloading it from the repository follow these steps:

1. Ensure that both [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) and [Docker](https://docs.docker.com/get-docker/) are installed.
2. Clone the repository with `git clone https://github.com/CDCgov/dibbs-ecr-refiner`.
3. Navigate to the top-level directory of this repository.
4. Run `docker build -t refiner .`.

## The API

When viewing these docs from the `/redoc` endpoint on a running instance of the Message Refiner or the DIBBs website, detailed documentation on the API will be available below.

## Architecture Diagram

```mermaid
flowchart LR

subgraph requests["Requests"]
direction TB
subgraph GET["fas:fa-download <code>GET</code>"]
hc["<code>/</code>\n(health check)"]
end
subgraph PUT["fas:fa-upload <code>PUT</code>"]
ecr["<code>/ecr</code>\n(refine eICR)"]
end
end

subgraph service[REST API Service]
direction TB
subgraph mr["fab:fa-docker container"]
refiner["fab:fa-python <code>refiner<br>HTTP:8080/</code>"]
refiner <==> db["fas:fa-database PostgreSQL"]
end
end

subgraph response["Responses"]
subgraph JSON["fa:fa-file-alt <code>JSON</code>"]
rsp-hc["fa:fa-file-code <code>OK</code> fa:fa-thumbs-up"]
end
subgraph XML["fas:fa-chevron-left fas:fa-chevron-right <code>XML</code>"]
rsp-ecr["fas:fa-file-code Refined eICR"]
end
end

hc -.-> mr -.-> rsp-hc
ecr ===> mr ===> rsp-ecr

```

## Additional notes on eICR Refinement

For further details on `<section>`, `<entry>`, and `<templateId>` elements, please see [eICR-Notes.md](eICR-Notes.md) for an explanation of trigger code `<templateId>`s, which sections they're in, and the `<observation>` data that should be returned in the refined eICR output.

```

```
