# Contributing to the DIBBs eCR Refiner

This document will outline how the DIBBs eCR Refiner application is structured and will provide details about how the team operates. Please feel free to open a PR with changes to this document if modifications or additions are needed!

## Architecture

The eCR Refiner consists of two primary components: a web application and an AWS Lambda function. This section will provide detail on each of these components.

### Web application

The web application component of the eCR Refiner allows users of the product to sign in and configure how the Refiner will process their eICR && RR files. The web app also allow users to do things like activate a configuration and test their in-progress configurations.

The technology used to build the web application is a [Vite-based React client](./client/) and a [Python-based FastAPI](./refiner/). The application will run as a Docker image defined by [Docker.app](./Dockerfile.app) in a production environment. Additionally, when running in production, the FastAPI server will serve the static client files.

### AWS Lambda

Once a jurisdiction has defined one or more configurations, their eICR/RR data will run through a version of the Refiner that runs on AWS Lambda. Running the Refiner on AWS Lambda allows for user's files to be processed by the Refiner in an event-based way. If an RR file triggers the Lambda's execution and a configuration has been defined for a condition in that RR file, the Refiner will automatically process it and drop the resulting output into a location where the jurisdiction is able to make use of the data.

The Lambda is also deployed as a Docker image in production. This image is defined by [Dockerfile.lambda](./Dockerfile.lambda).

### Web App 🤝 Lambda

While the web application can be used without the Lambda, the Lambda cannot be used without the web application. The Lambda allows the Refiner to run on every incoming eICR/RR pair, however, configurations must be created by users within the web application before processing can occur.

Running the refining process on a pair of files can be done within the web application itself, but there is no way to run many files through it in an automated way. That's why the Lambda is a crucial component.

The web application (`refiner`) and AWS Lambda (`lambda`) Docker image builds are stored in the [dibbs-ecr-refiner GHCR repository](https://github.com/orgs/CDCgov/packages?repo_name=dibbs-ecr-refiner). When a branch is merged into `main`, both of these images will be built, tagged as `latest` and `main`, and stored here.
