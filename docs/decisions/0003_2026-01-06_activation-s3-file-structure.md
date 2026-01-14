# 3. S3 file structure for activations

Date: 2026-01-06

## Status

Proposed

## Context and Problem Statement

The eCR Refiner application is composed of two distinct parts: The web application and an AWS Lambda. The web application has full access to a PostgreSQL RDS database that stores user, condition, and confguration information. Both the web application and the database will live in a public AWS VPC that can be accessed by users via the internet in order to allow them to log in and set up their condition configurations.

The Lambda - a version of the Refiner code that will be automatically triggered via AWS SQS - will not be able to access the database due to living in the private VPC that is not internet accessible. In order for the Lambda version of the Refiner to work, we must figure out a way to provide activated configuration information without RDS being involved.

In order to solve this problem, we have decided to take the following path:

1. User sets up configuration via the public web application
2. User activates the configuration
3. During the activation step, the web application serializes the configuration into a file format that will be consumed by Lambda, uploads it into a public S3 bucket
4. Lambda in a private VPC is triggered by SQS, attempts to find configuration file in public S3 bucket, deserializes file, runs refining process and outputs results

The goal of this proposal is to provide detail around how the S3 bucket will be used for storing configuration activation files on a per-jurisdiction basis. Once the pull request containing this document is merged we should have a clear, well-defined implementation plan and can begin executing on this work immediately.

This document will provide information on the following topics:

- Directory naming convention
- File naming convention
- File identification process used by Lambda
- Required activation logic updates
- Required deactivation logic updates
- Handling failures
- Activation file metadata
- Ensuring database and file consistency

This top section will describe the problems and offer some potential solutions. Please jump to my recommendations in [this section](#decision-outcome).

### Directory naming and identification by Lambda

When the Lambda receives an SQS message, it will contain information that describes where the eICR and RR files are located. The Refiner will attempt to fetch both of these files. Once it has this information, it will parse the RR for the following data:

- Jurisdiction ID
- Reportable condition codes

Using this info, it must check to see if the jurisdiction has an active configuration for a reportable condition code. If a configuration file exists, run the refining process using it. If a configuration file does not exist, the refining process can be skipped and it'll move on to the next condition code. At the end, the files will be outputted.

In order to accommodate this process, we will likely want to structure the S3 bucket like this:

1. Top-level directory contains a sub-directory per jurisdiction
2. Jurisdiction directory contains sub-directories matching the condition code for each activated configuration
3. The condition code directory will contain two files: an activation file used by the Lambda and a metadata file

The S3 bucket will be structured like this:

```sh
.
└── {jurisdiction ID}/
    └── {condition code}/
        ├── current.json
        └── {version}/
            ├── active.json
            └── metadata.json
```

Using the jurisdiction ID, condition, and version the Refiner can attempt to find an `active.json` file for a condition. If it exists, the Refiner can consume it.

#### Conditions with multiple child RSG codes - multiple activation files (option 1)

Something to consider is that each condition may have more than one child condition code. One approach to handling this is to allow the web application to create an `active.json` file per child condition code and write it to the expected path in S3. This would effectively create a duplicate activation file for each code.

For example, the SDDH jurisdiction's first COVID-19 activation would generate these two activation files:

```sh
.
└── SDDH/
    ├── 186747009/
    │   └── 1/
    │       └── active.json
    └── 840539006/
        └── 1/
            └── active.json
```

This does, however, break the concept of having a single `s3_url` tied to a single configuration. We would need to rethink this if we took this approach.

#### Conditions with multiple child RSG codes - mapping strategy (option 2)

Another potential route we could take in order to handle multiple condition codes could be to generate and include a mapping file as part of the Lambda package. When a condition code is received by the Lambda, it uses the value to see if that code maps to another "dominant" code if the specified file path does not exist.

For example, a COVID-19 activation would generate this activation file for the `SDDH` jurisdiction:

```sh
.
└── SDDH/
    └── 186747009/
        └── 1/
            └── active.json
```

We only have a single file but we have two possible COVID-19 child RSG codes: `186747009` and `840539006`. If the Refiner receives `186747009` the activation file will be found and used. However, if the Refiner receives `840539006` instead no file will be found. In this case, the Refiner would need to check the map using `840539006` as the key, which would point to the "dominant" value we determine for COVID-19 and use the file from that path instead.

This method involves a pre-computed mapping file that we'd need to create and maintain along with introducing additional work for the Lambda (multiple possible file path checks instead of one).

### Required updates to application activation logic

The concept of activations has already been built and is usable in the application today. We will, however, need to update the application further to serialize the configuration information and write it to the S3 bucket.

The activation logic to write the files will need to be something like this:

1. Open a database transaction
2. Create serialized activation file(s)
3. Create metadata file(s)
4. Write all files to S3
5. Update configuration row in database (include S3 URL(s))
6. Commit database transaction

We need to ensure that both writing to S3 and writing to the database are successful in order for an activation to be considered successful. If one of these steps fail then we need to provide an error message to the user that lets them know to try again.

More in-depth details on this later in the document, including handling failures.

### Required updates to application deactivation logic

Similar to activations, deactivation handling will also need to be updated to add S3 modifications into the workflow.

The deactivation logic will need to be something like this:

1. Open a database transaction
2. Delete condition code directory (or directories) from S3
3. Update configuration row in database (remove S3 URL(s))
4. Commit database transaction

More in-depth details on this later in the document, including handling failures.

### Activation file metadata

As mentioned earlier, each condition code directory should contain two files:

- `active.json` - the serialized configuration file that will be read, deserialized, and used by the Lambda
- `metadata.json` - a file containing metadata about the configuration

The metadata file will not be used by the Refiner. It will serve only as a piece of data to help us debug issues and/or compare against a configuration record in the database.

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

Problem #1 likely wouldn't be a big issue for Refiner since the max configuration number will not be extremely high. Problem #2 is not ideal but could be used as a backup for the idea described in the next section. Lastly, and most importantly, problem #3 is something we'd need to dig into more to know if this is a viable option. If the Lambda does not read directly from the public bucket but is instead replicated, this will introduce additional complexity.

#### Event driven

Another idea is to forgo any sort of regular automated integrity checking in favor of an event driven approach. The "events" in this case would be user actions in the UI that impact activation and deactivation. As described above, the database will always be the source of truth, the data flow is always one way, and the data in the S3 bucket will not be modified by other processes outside of the web app.

The only time the S3 data will be modified is during an activation or a deactivation. If we can guarantee that:

1. S3 files are written
2. Configuration database row is updated

We can be confident that these objects are accurate and in sync. Additionally, we can increase safety during activations and deactivations by making use of a pointer file that Lambda will read from to determine the action it will take. More on this in the outcomes section.

## Decision Outcome

Below are my recommendations for each of the problems described above.

### Directory and file naming

For **directory and file naming** I propose we use the following format:

```sh
.
└── {jurisdiction ID}/
    └── {condition code}/
        ├── current.json
        └── {version}/
            ├── active.json
            └── metadata.json
```

- `jurisdiction ID` - the ID of the jurisdiction (comes from parsing the RR)
- `condition code` - the child RSG SNOMED code of the condition (comes from parsing the RR)
- `version` - the version of the configuration
- `active.json` - the file containing the serialized version of a condition configuration, used by Lambda for the refining process
- `metadata.json` - the file containing metadata about the activation, condition, and configuration. Not used by any automated process, informational only for the time being
- `current.json` - the file controlling how Lambda operates and on what version of a configuration it interacts with. This is explained in more detail in the next section

#### current.json

As mentioned above, I am proposing that each condition code directory contain a `current.json` at this path: `{jurisdiction ID}/{condition code}/current.json`. This file will be created upon a user activating the configuration within their jurisdiction. This file will be read and parsed by Lambda to determine which version of a configuration to use (or not, if `version` is `null` or the file is missing). This file is a pointer for Lambda that can be updated by the web application without causing any negative impacts to the "always on" processing that the Lambda is doing.

> [!IMPORTANT]
> Lambda will treat a missing `current.json` as the configuration being inactive. No processing will be attempted.

The structure of `current.json` will be:

```json
{
    "version": 2
}
```

- `version` - the integer version of the currently active configuration, or `null` if inactive

Once the Lambda receives the jurisdiction ID and reportable condition codes from the RR, it can check which versioned sub-directory it should be using.

The main goal in using this file is to handle failures gracefully and without causing interruption to Lambda. We are able to enable/disable the Lambda's processing and/or point it to use a different configuration version without potentially deleting files it may be trying to use.

### Managing conditions with multiple child RSG SNOMED codes

For **managing conditions with multiple child RSG SNOMED codes** create an S3 file path for each child code.

This is the preferred path forward because:

- Lambda parses the RR and then checks to see if the path exists or not. No complicated logic required
  - This will create a duplicate of the activation file, but storage is cheap and this will simplify the work that needs to be done by Lambda
- No need to create, maintain, and ship any pre-computed map that Lambda would need to check
- The `s3_url` column on a configuration is only for record keeping, so we can easily change this into an array or its own table
- The web application will handle all of the complex processing during activation and deactivation. This is preferable since we'd like to make sure Lambda does as little work as possible

The main downsides to this approach are:

- Duplicating data in S3
- During activation and deactivation, the web app will need to handle writing and uploading many different files to S3

That said, this is still a less complex solution compared to mapping.

### Web application updates for activation

We cannot guarantee that all individual actions that make up an activation will succeed. We also need to consider that the Lambda will continue processing data while activation is happening.

Activation will work as follows, using `SDDH` as a sample jurisdiction and version 1 of a COVID-19 configuration:

1. Open a database transaction
2. Create a serialized file per condition child RSG code
3. Create a metadata file per condition child RSG code
4. Write all files to their respective paths within the jurisdiction directory (replace existing files)
5. Verify all file uploads succeeded
6. Write or update all `current.json` files to point to the newly active version
7. Update configuration row in database
8. Commit database transaction

#### Activation - Successful outcome

A successful activation will produce the following changes:

1. In S3, these files will be written

    ```sh
    .
    └── SDDH/
        ├── 186747009/
        │   ├── current.json
        │   └── 1/
        │       ├── active.json
        │       └── metadata.json
        └── 840539006/
            ├── current.json
            └── 1/
                ├── active.json
                └── metadata.json
    ```

2. The database row of the version 1 COVID-19 configuration for SDDH will have its status set to `active` and its `s3_urls` will include the URLs for the two active configuration files written.

#### Activation - Failure outcome

A failed activation will produce the following changes:

1. In S3, only some of the necessary files could be written. Note that we're missing this directory's `current.json` and the entire subdirectory for `840539006`

    ```sh
    .
    └── SDDH/
        └── 186747009/
            └── 1/
                ├── active.json
                └── metadata.json
    ```

2. In this scenario, only 2 of the necessary files were written so the activation will fail
3. Database transaction ends, record is not updated, user is given an error message in the web app
4. Lambda continues processing without issue since no `current.json` file exists

#### Activation - Retrying a failed activation

Retrying a failed activation should work similarly to a typical activation. The main difference is that files produced by a failed activation may already exist.

During the retry we should attempt to write files to the paths we need them at regardless of whether they exist already or not.

### Web application updates for deactivation

We should not delete any files during a deactivation. The reason being that the Lambda continues to process data regardless of whether files are being modified via the web app.

If a user goes to deactivate a configuration, we should modify the `current.json` for each child RSG code that condition maps to. This will leave configuration files in place while effectively deactivating the Refiner for a reportable condition code.

#### Deactivation - Successful outcome

If jurisdiction `SDDH` deactivates their version 3 COVID-19 configuration, the following results are produced:

1. `current.json` is updated within each directory from `{"version": 3}` to `{"version": null}`, representing the deactivation
2. When Lambda reads `SDDH/186747009/current.json` or `SDDH/840539006/current.json` it will see the `current.json`'s `version` is `null` and will skip processing for that condition code
3. SDDH's version 3 COVID-19 configuration in the database has its `status` set to `inactive`

#### Deactivation - Failure outcome

A deactivation failure means that one or both of these two operations failed:

- The `current.json`'s new `version` value couldn't be written to S3
- The configuration's `status` update in the database was unsuccessful

In order to address this we should:

1. Try to update `current.json` files first since this is ultimately what the Lambda is relying on
2. Ensure deactivation can be safely retried upon failure

A retry would mean:

1. Cycling through all child RSG codes and setting their `current.json` value to `null`, even if they are already `null`
2. Setting the `active` configuration to `inactive` after S3 updates occur

This can be event driven: if S3 actions fail but the configuration remains `active` in the web application, we can allow the user to attempt deactivation again. The application will try to go through the same process as it did previously.

### Metadata file

As mentioned earlier, I propose we add some basic information to the metadata file as a starting point. We can freely update the content of this file at a later time if we decide more or less info is needed.

I suggest we include the following information to get us started:

- Condition canonical URL
- TES version number of the condition
- Condition name
- Configuration version number
- List of condition child RSG SNOMED codes (or S3 URLs to related directories)

The initial format of this file will look as such:

```json
{
    "canonicalUrl": "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64",
    "tesVersion": "3.0.0",
    "conditionName": "COVID-19",
    "configurationVersion": 3,
    "childRsgSnomedCodes": [186747009,840539006]
}
```

### Tickets

Epic: [[EPIC] Production Activation (Lambda)](https://github.com/CDCgov/dibbs-ecr-refiner/issues/401)

Tickets will be created or updated as needed to be relevant to the plan described in this document.

### Real life scenario example

The purpose of this section is to give a full, real-world example demonstrating how a user within a jurisdiction may interact with the application and the result it will have on the Lambda's processing.

For this demo, we'll assume the following:

Jurisdiction ID: `SDDH`
Condition: Influenza

#### Step 1: Activate for the first time

SDDH user successfully activates the Influenza configuration for the first time, which is also the first ever configuration activation for the jurisdiction.

Changes that occur in the database:

- Influenza database record is updated
  - `status` changes from `draft` to `active`
  - `last_activated_at` is set to the current time
  - `last_activated_by` is set to the user's ID

Changes that occur in S3:

- Jurisdiction directory `SDDH` is created
- Influenza has 8 child RSG groupers, so a subdirectory is created for each
  - `541131000124102`
  - `43692000`
  - `6142004`
  - `725894000`
  - `77282800`
  - `95891005`
  - `719590007`
  - `661761000124109`
- A `current.json` is written to every subdirectory and contains `"version": 1`
- A `/1/metadata.json` file is written for every subdirectory
- A `/1/active.json` file is written for every subdirectory

The end result in S3 looks like this:

```sh
.
└── SDDH/
    ├── 541131000124102/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 43692000/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 6142004/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 725894000/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 77282800/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 95891005/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 719590007/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    └── 661761000124109/
        ├── current.json
        └── 1/
            ├── active.json
            └── metadata.json
```

#### Step 2: Influenza is deactivated

SDDH user successfully deactivates the Influenza configuration.

Changes that occur in the database:

- Influenza database record is updated
  - `status` changes from `active` to `inactive`

Changes that occur in S3:

- Every condition code subdirectory has its `current.json` `version` set to `null`

The end result in S3 looks like this:

```sh
.
└── SDDH/
    ├── 541131000124102/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 43692000/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 6142004/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 725894000/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 77282800/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 95891005/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 719590007/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    └── 661761000124109/
        ├── current.json
        └── 1/
            ├── active.json
            └── metadata.json
```

#### Step 3: Influenza is activated again

SDDH user successfully reactivates the existing Influenza configuration after previously deactivating it.

Changes that occur in the database:

- Influenza database record is updated
  - `status` changes from `inactive` to `active`

Changes that occur in S3:

- Every condition code subdirectory has its `current.json` `version` set to `1`

The end result in S3 looks like this:

```sh
.
└── SDDH/
    ├── 541131000124102/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 43692000/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 6142004/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 725894000/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 77282800/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 95891005/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    ├── 719590007/
    │   ├── current.json
    │   └── 1/
    │       ├── active.json
    │       └── metadata.json
    └── 661761000124109/
        ├── current.json
        └── 1/
            ├── active.json
            └── metadata.json
```

> [!IMPORTANT]
> The activation logic needs to validate that all files that should exist do exist. If they do not, they must be written.

#### Step 4: Influenza draft is created and then activated

SDDH user successfully activates their version 2 Influenza draft.

Changes that occur in the database:

- Influenza version 1 configuration record is updated
  - `status` changes from `active` to `inactive`
- Influenza version 2 draft configuration record is updated
  - `status` changes from `draft` to `active`

Changes that occur in S3:

- A `/2/active.json` file is written for every subdirectory
- A `/2/metadata.json` file is written for every subdirectory
- A `current.json` is updated in every existing subdirectory to contain `"version": 2`

The end result in S3 looks like this:

```sh
.
└── SDDH/
    ├── 541131000124102/
    │   ├── current.json
    │   ├── 1/
    │   │   ├── active.json
    │   │   └── metadata.json
    │   └── 2/
    │       ├── active.json
    │       └── metadata.json
    ├── 43692000/
    │   ├── current.json
    │   ├── 1/
    │   │   ├── active.json
    │   │   └── metadata.json
    │   ├── 2
    │   ├── active.json
    │   └── metadata.json
    ├── 6142004/
    │   ├── current.json
    │   ├── 1/
    │   │   ├── active.json
    │   │   └── metadata.json
    │   └── 2/
    │       ├── active.json
    │       └── metadata.json
    ├── 725894000/
    │   ├── current.json
    │   ├── 1/
    │   │   ├── active.json
    │   │   └── metadata.json
    │   └── 2/
    │       ├── active.json
    │       └── metadata.json
    ├── 77282800/
    │   ├── current.json
    │   ├── 1/
    │   │   ├── active.json
    │   │   └── metadata.json
    │   └── 2/
    │       ├── active.json
    │       └── metadata.json
    ├── 95891005/
    │   ├── current.json
    │   ├── 1/
    │   │   ├── active.json
    │   │   └── metadata.json
    │   └── 2/
    │       ├── active.json
    │       └── metadata.json
    ├── 719590007/
    │   ├── current.json
    │   ├── 1/
    │   │   ├── active.json
    │   │   └── metadata.json
    │   └── 2/
    │       ├── active.json
    │       └── metadata.json
    └── 661761000124109/
        ├── current.json
        ├── 1/
        │   ├── active.json
        │   └── metadata.json
        └── 2/
            ├── active.json
            └── metadata.json
```

#### Step 5: Influenza deactivation fails

SDDH user unsuccessfully attempts to deactive Influenza.

Changes that occur in S3:

- 3/8 `current.json` files are updated to `"version": null` and then writes to S3 begin failing

Changes that occur in the database:

- Influenza configuration record is unchanged
  - `status` is still `active`

The end result in S3 looks like this:

- Unchanged from previous step

Recovery:

- Configuration is still `active` so the user can attempt to set it to `inactive` again
- Deactivation logic is idempotent and all `current.json` file updates can be attempted once again

User deactivates the configuration successfully.

#### Step 6: User creates a Down Syndrome draft and unsuccessfully activates it

SDDH user unsuccessfully attempts to activate their Down Syndrome draft.

Changes that occur in S3:

- `41040004` subdirectory is created
- `/1/active.json` file is created

Writing the metadata file fails and the activation process fails.

- Down Syndrome configuration record is unchanged
  - `status` is still `draft`

The end result in S3 looks like this:

```sh
.
└── SDDH/
    ├── 41040004/ <-- Down Syndrome
    │   └── 1/
    │       └── active.json
    ├── 541131000124102/
    │   ├── current.json
    │   ├── 1/
    │   │   ├── active.json
    │   │   └── metadata.json
    │   └── 2/
    │       ├── active.json
    │       └── metadata.json
    ├── 43692000/
    │   ├── current.json
    │   ├── 1/
    │   │   ├── active.json
    │   │   └── metadata.json
    │   ├── 2
    │   ├── active.json
    │   └── metadata.json
    ├── 6142004/
    │   ├── current.json
    │   ├── 1/
    │   │   ├── active.json
    │   │   └── metadata.json
    │   └── 2/
    │       ├── active.json
    │       └── metadata.json
    ├── 725894000/
    │   ├── current.json
    │   ├── 1/
    │   │   ├── active.json
    │   │   └── metadata.json
    │   └── 2/
    │       ├── active.json
    │       └── metadata.json
    ├── 77282800/
    │   ├── current.json
    │   ├── 1/
    │   │   ├── active.json
    │   │   └── metadata.json
    │   └── 2/
    │       ├── active.json
    │       └── metadata.json
    ├── 95891005/
    │   ├── current.json
    │   ├── 1/
    │   │   ├── active.json
    │   │   └── metadata.json
    │   └── 2/
    │       ├── active.json
    │       └── metadata.json
    ├── 719590007/
    │   ├── current.json
    │   ├── 1/
    │   │   ├── active.json
    │   │   └── metadata.json
    │   └── 2/
    │       ├── active.json
    │       └── metadata.json
    └── 661761000124109/
        ├── current.json
        ├── 1/
        │   ├── active.json
        │   └── metadata.json
        └── 2/
            ├── active.json
            └── metadata.json
```

Recovery:

This failure occurred because `metadata.json` could not be written. Because of this `metadata.json` and `current.json` are missing for Down Syndrome.

In order to recover from this failure the user attempts to activate the Down Syndrome configuration again since it remained in `draft`. Lambda will not do any processing on Down Syndrome since the `current.json` is missing.

The activation is successful next time around.

## Links

I used this to create these nice directory trees: [https://tree.nathanfriend.com/](https://tree.nathanfriend.com/)
