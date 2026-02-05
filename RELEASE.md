# eCR Refiner Release Process

This document will outline the process for releasing a new version of the eCR Refiner web application and AWS Lambda function, along with roles and responsibilites of those involved in the release process.

## Create the release notes (engineer)

This step will be performed by an **engineer**.

1. Navigate to the [GitHub Releases page](https://github.com/CDCgov/dibbs-ecr-refiner/releases) and click `Draft a new release`
2. Create a new release candidate (rc) tag that follows [semantic versioning](https://semver.org/) (e.g. `3.6.7-rc1` (no "v" in front), targeting the `main` branch
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

## Testing the release candidate (engineer)

This step will be performed by an **engineer**.

TBD

## Publish the release

This step will be performed by an **engineer**.
