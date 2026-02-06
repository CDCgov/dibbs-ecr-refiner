# eCR Refiner Release Process

This document will outline the process for releasing a new version of the eCR Refiner web application and AWS Lambda function, along with roles and responsibilites of those involved in the release process.

## Create the release notes (engineer)

This step will be performed by an **engineer**.

1. Navigate to the [GitHub Releases page](https://github.com/CDCgov/dibbs-ecr-refiner/releases) and click `Draft a new release`
2. Create a new release candidate (rc) tag that follows [semantic versioning](https://semver.org/) (e.g. `3.6.7-rc1`), targeting the `main` branch
3. After creating the tag you’ll be able to confirm your previous tag and the `Generate release notes` button will become clickable. Click it!
4. At the bottom of the page click `Save draft`
5. Let a product team member know that a new draft release is ready for editing

## Edit the release notes (product)

This step will be performed by **product**.

1. Navigate to the [GitHub Releases page](https://github.com/CDCgov/dibbs-ecr-refiner/releases) and click on the draft release's pencil icon to edit it
2. Edit down the generated notes as needed (excluding things such as test updates, refactors, dependency bumps, chores, etc.)
3. Add the template release notes linked here to the notes. These should mostly be for product to write up to inform users of changes to the application
4. **Set as pre-release**: Before publishing, ensure that the “Set as a pre-release” checkbox is marked. The release should not be marked as the latest release until deployment and testing have been performed. Then click “save as draft”!
5. Let an engineering team member know the release notes are complete

## Add release notes link to app (engineer)

This step will be performed by an **engineer**.

Open a PR that adds the link to the release notes and a summary of the release to the App Updates page.

> [!IMPORTANT]
> This PR needs to be merged before proceeding further.

## Testing the release candidate (engineer)

This step will be performed by an **engineer**.

Communicate with partners to get the release candidate containers deployed to testing environments.

### Testing steps

TBD

## Build final release images (engineer)

This step will be performed by an **engineer**.

With the containers deployed and the testing completed, we can now create the final release tag.

1. Navigate to the [GitHub Releases page](https://github.com/CDCgov/dibbs-ecr-refiner/releases) and create a new release with the final release tag (no `-rc` at the end)
2. Copy the notes from the pre-release into the final release
3. Create a build and push the images to GHCR and ECR using the [build/push job](https://github.com/CDCgov/dibbs-ecr-refiner/actions/workflows/docker-image-push.yml)
    1. Make sure the git ref is the release candidate tag
    2. Make sure the version is the same as the release candidate tag without `-rc` at the end
    3. Make sure the images will be pushed to both GHCR and ECR
4. Let partners know images have been built and are ready for deployment

## Publish the release (engineer)

This step will be performed by an **engineer**.

1. Once the new containers are running in production go edit the release notes once more, mark it as the latest release, and publish them
2. Release is complete!
