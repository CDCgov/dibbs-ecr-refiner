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
2. The job will push the new RC images to GHCR, which are ready to be deployed and tested. These images can be found at:
    - [refiner](https://github.com/CDCgov/dibbs-ecr-refiner/pkgs/container/dibbs-ecr-refiner%2Frefiner)
    - [lambda](https://github.com/CDCgov/dibbs-ecr-refiner/pkgs/container/dibbs-ecr-refiner%2Flambda)
    - [ops](https://github.com/CDCgov/dibbs-ecr-refiner/pkgs/container/dibbs-ecr-refiner%2Fops)
3. The job will also publish draft pre-release release notes that can be found on the [releases page](https://github.com/CDCgov/dibbs-ecr-refiner/releases)

## Edit the release notes (product)

This step will be performed by **product**.

1. Navigate to the [GitHub Releases page](https://github.com/CDCgov/dibbs-ecr-refiner/releases) and click on the draft release's pencil icon to edit it
2. Edit down the generated notes as needed (excluding things such as test updates, refactors, dependency bumps, chores, etc.)
3. Add the template release notes linked here to the notes. These should mostly be for product to write up to inform users of changes to the application
4. **Set as pre-release**: Before publishing, ensure that the “Set as a pre-release” checkbox is marked. The release should not be marked as the latest release until deployment and testing have been performed. Then click “save as draft”
5. Let an engineering team member know the release notes are complete

## Add release notes link to app (engineer)

This step will be performed by an **engineer**.

TBD

~~Open a PR that adds the link to the release notes and a summary of the release to the App Updates page.~~

> [!IMPORTANT]
> ~~This PR needs to be merged before proceeding further.~~

## Testing the release candidate (engineer)

This step will be performed by an **engineer**.

Communicate with partners to get the release candidate containers deployed to testing environments.

### Testing steps

TBD

## Build final release images (engineer)

This step will be performed by an **engineer**.

With the RC containers deployed and the testing completed, we can now create the final release tag.

1. Create a build and push the images to GHCR and ECR using the [build/push job](https://github.com/CDCgov/dibbs-ecr-refiner/actions/workflows/docker-image-push.yml)
    1. Make sure the git ref is the release candidate tag (e.g., `1.4.0-rc.1`)
    2. Make sure the version is the same as the release candidate tag without `-rc` at the end (e.g., `1.4.0`)
    3. Make sure the images will be pushed to both GHCR and ECR
    4. Make sure creating release notes is checked
2. Let partners know images have been built and are ready for deployment
3. Navigate to the [GitHub Releases page](https://github.com/CDCgov/dibbs-ecr-refiner/releases) and edit the new release with the final release tag (no `-rc` at the end)
4. Copy the notes from the pre-release into the final release

## Publish the release (engineer)

This step will be performed by an **engineer**.

> [!IMPORTANT]
> Coordinate with product on when to perform these last actions.

1. Once the new containers are running in production go edit the release notes once more, mark it as the latest release, and hit publish
2. Release is complete!
