# eCR Refiner Release Process

This document will outline the process for releasing a new version of the eCR Refiner web application and AWS Lambda function, along with roles and responsibilites of those involved in the release process.

## Create the release candidate (engineer)

This step will be performed by an **engineer**.

Before creating a stable release, we need to create release candidate images that can be tested.

1. Run the [release candidate builder job](https://github.com/CDCgov/dibbs-ecr-refiner/actions/workflows/build-release-candidate.yml) using the following inputs:
    1. `ref` = `main`
    2. `version` = Semantic version to use (example: `1.4.0`)
    3. `rc` = the RC number (example: `rc.1`)
    4. `dry_run` = `false` (feel free to try using `true` first if you'd like to run a test without creating anything)
2. The job will push the new RC images to ECR and GHCR, which are ready to be deployed and tested. These images can be found at:
    - [refiner](https://github.com/CDCgov/dibbs-ecr-refiner/pkgs/container/dibbs-ecr-refiner%2Frefiner)
    - [lambda](https://github.com/CDCgov/dibbs-ecr-refiner/pkgs/container/dibbs-ecr-refiner%2Flambda)
    - [ops](https://github.com/CDCgov/dibbs-ecr-refiner/pkgs/container/dibbs-ecr-refiner%2Fops)

## Testing the release candidate (engineer)

This step will be performed by an **engineer**.

Communicate with partners to get the release candidate containers deployed to testing environments. Do not proceed until partners notify us that testing was successful.

## Build final release images (engineer)

This step will be performed by an **engineer**.

We can now create the final release tag.

1. Create a build and push the images to GHCR and ECR using the [release candidate promotion job](https://github.com/CDCgov/dibbs-ecr-refiner/actions/workflows/promote-release-candidate.yml)
    1. Make sure the `rc_version` is the release candidate tag (e.g., `1.4.0-rc.1`)
    2. Make sure the `version` is the same as the release candidate tag without `-rc.x` at the end (e.g., `1.4.0`)
    3. Leave `dry_run` unchecked
2. Run the job
3. Check that the images were successfully pushed to both GHCR and ECR (see job logs)
4. Let partners know images have been built and are ready for deployment

## Publish the release notes (product)

This step will be performed by **product**.

1. Navigate to the [release page](https://github.com/CDCgov/dibbs-ecr-refiner/releases)
2. Find the draft release notes with the title containing the version of this release
3. Edit the release notes
4. When complete, select `Publish release`
