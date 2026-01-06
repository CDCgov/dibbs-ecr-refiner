# 3. S3 file structure for activations

Date: 2026-01-06

## Status

Proposed

## Context and Problem Statement

The eCR Refiner application is composed of two distinct parts: The web application and an AWS Lambda. The web application has full access to a PostgreSQL RDS database that stores user, condition, and confguration information. Both the web application and the database will live in a public AWS VPC that can be accessed by users via the internet in order to allow them to log in and set up their condition configurations.

The Lambda - a version of the Refiner code that will be automatically triggered via AWS SQS - will not be able to access the database due to living in the private VPC that is not internet accessible. In order for the Lambda version of the Refiner to work, we must figure out a way to provide activated configuration information without RDS being involved.

In order to solve this problem, we have decided to take the following path:

1. User sets up configuration via the public web application
2. User activates their condition
3. During the activation step, the web application serializes the configuration into a file format that will be consumed by Lambda, uploads it into a public S3 bucket
4. Private Lambda is triggered by SQS, attempts to find configuration file in public S3 bucket, deserializes file, runs refining process and outputs results

The goal of this proposal is to provide detail around how the S3 bucket will be used for storing configuration activation files on a per-jurisdiction basis. Once the pull request containing this document is merged we should have a clear, well-defined implementation plan and can begin executing on this work immediately.

This document will provide information on the following topics:

- Directory naming convention
- File naming convention
- File identification process used by Lambda
- Required activation logic updates
- Required deactivation logic updates
- Activation file metadata
- Ensuring database and file consistency

### Directory naming and identification by Lambda

When the Lambda receives an SQS message, it will contain information that describes where the eICR and RR files can be located. The Refiner will attempt to fetch both of these files. Once it has this information, it will parse the RR for the following data:

- Jurisdiction ID
- Condition codes

Once the Refiner has this information it must check to see if the jurisdiction has an active configuration per serialized configuration file. If a configuration file exists, run the refining process using it. If a configuration file does not exist, the refining process can be skipped and it'll move on to the next condition code. At the end, the files will be outputted.

In order to accommodate this process, we should organize the S3 bucket as such:

1. Top-level directory contains a sub-directory per jurisdiction
2. Jurisdiction directory contains sub-directories matching the condition code for each activated configuration
3. The condition code directory will contain two files: an activation file used by the Lambda and a metadata file

The S3 bucket will be structured like this:

```sh
{jurisdiction ID}/{condition code}/active.json
{jurisdiction ID}/{condition code}/metadata.json
```

Using the jurisdiction ID and condition the Refiner can attempt to find an `active.json` file for a condition. If it exists, the Refiner can consume it.

#### Conditions with multiple child RSG codes - multiple activation files (option 1)

Something to consider is that each condition may have more than one child condition code. One approach to handling this is to allow the web application to create an `active.json` file per child condition code and write it to the expected path in S3. This would effectively create a duplicate activation file for each code.

For example, a COVID-19 activation would generate these two activation files for the `SDDH` jurisdiction:

```sh
SDDH/186747009/active.json
SDDH/840539006/active.json
```

This does, however, break the concept of having a single `s3_url` tied to a single configuration. We would need to rethink this if we took this approach.

#### Conditions with multiple child RSG codes - mapping strategy (option 2)

Another potential route we could take in order to handle multiple condition codes could be to generate and include a mapping file as part of the Lambda package. When a condition code is received by the Lambda, it uses the value to see if that code maps to another possible if the specified file path does not exist.

For example, a COVID-19 activation would generate this activation file for the `SDDH` jurisdiction:

```sh
SDDH/186747009/active.json
```

We only have a single file but we have two possible COVID-19 child RSG codes: `186747009` and `840539006`. If the Refiner receives `186747009` the activation file will be found and used. However, if the Refiner receives `840539006` instead no file will be found. In this case, the Refiner would need to check the map using `840539006` as the key, which would point to the "dominant" value we determine for COVID-19 and use the file from that path instead.

##### Proposal

Multiple copies of the same activation file per child code seems like the more straightforward route to take. This enables us to stick with the idea of a path either existing or not existing without extra work needing to be done by the Lambda to try to determine if the file lives elsewhere. S3 storage is also very cheap, so this should not cause budget issues.

This does mean that a configuration may now map to multiple S3 URLs upon serializing and saving the file. We should create a join table or store this information as an array on a configuration record.

### Required updates to application activation logic

The concept of activations has already been built and is usable in the application today. We will, however, need to update the application further to serialize the configuration information and write it to the S3 bucket.

I propose we update the activation step to include the following:

1. Open a database transaction
2. Create serialized activation file(s)
3. Create metadata file(s)
4. Write all files to S3
5. Update configuration row in database (include S3 URL(s))
6. Commit database transaction

We need to ensure that both writing to S3 and writing to the database are successful in order for an activation to be considered successful. If one of these steps fail then we need to provide an error message to the user that lets them know to try again.

### Required updates to application deactivation logic

Similar to activations, deactivation handling will also need to be updated to add S3 modifications into the workflow.

I propose we update the deactivation step to include the following:

1. Open a database transaction
2. Delete condition code directory (or directories) from S3
3. Update configuration row in database (remove S3 URL(s))
4. Commit database transaction

### Activation file metadata

As mentioned earlier, each condition code directory should contain two files:

- `active.json` - the serialized configuration file that will be read, deserialized, and used by the Lambda
- `metadata.json` - a file containing metadata about the configuration

The metadata file will not be used by the Refiner. It will only serve as a piece of data to help us debug issues and/or compare against a configuration record in the database.

#### Metadata inclusions

There are various pieces of information that may make sense to include in the metadata file, such as:

- Condition canonical URL
- TES version number of the condition
- Condition name
- Configuration version number

Since this file will not be used by any technical process we will be free to change it over time as we see fit.

### Ensuring database and file consistency

When it comes to ensuring the data in the database matches the S3 file that will be used by the Lambda, we need to consider the "source of truth". In this case it will always be the database since the user will be modifying this data via the web application. Updating a configuration and activating it will produce a new file in S3. This data is always one way, from the web app to S3.

I will outline a few approaches we could take to ensure that S3 data and the database stay in sync.

#### Polling

The application (or an external process) finds all currently activated configurations and performs a data check against the files that exist in S3. If the check files, the process will perform a repair and log an event. This process would run on a regular schedule.

While this could work, it:

1. Doesn't scale very well
2. Catches problems late
3. Assumes the public S3 bucket is being used directly by the web app and the Lambda (what if the data is replicated to a private bucket?)

#### Event driven

Another idea is to forgo any sort of regular automated integrity checking in favor of an event driven approach. As described above, the database will always be the source of truth, the data flow is always one way, and the data in the S3 bucket will not be modified by other processes.

The only time the S3 data will be modified is during an activation or a deactivation. If we can guarantee that:

1. S3 files are written
2. Configuration database row is updated

We can be confident that these objects are in sync. With good integration testing in place, I lean strongly towards this approach over polling.

## Decision Drivers

What metrics or factors drove your decision?

## Considered Options

What other options were considered, and what pros and cons exist around these decisions?

## Decision Outcome

What decision did you go forward with, and how does it map to the above decision drivers?

## Appendix (OPTIONAL)

Add any links here that are relevant for understanding your proposal or its background.

**Be sure to read the information about this in [CONTRIBUTING](https://github.com/CDCgov/dibbs-ecr-refiner/blob/main/CONTRIBUTING.md##Request-for-comment)**
