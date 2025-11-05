# Contributing to the DIBBs eCR Refiner

This document will outline how the DIBBs eCR Refiner application is structured and will provide details about how the team operates. Please feel free to open a PR with changes to this document if modifications or additions are needed!

## Getting started

Please refer to the project's [README](./README.md/#running-the-project-locally) which describes how to get the project running on your local machine once you've cloned down the repository.

## Architecture

The eCR Refiner consists of two primary components: a web application and an AWS Lambda function. This section will provide detail on each of these components.

### Web application

The web application component of the eCR Refiner allows users of the product to sign in and configure how the Refiner will process their eICR & RR files. The web app also allow users to do things like activate a configuration and test their in-progress configurations.

The technology used to build the web application is a [Vite-based React client](./client/) and a [Python-based FastAPI](./refiner/). The application will run as a Docker image defined by [Docker.app](./Dockerfile.app) in a production environment. Additionally, when running in production, the FastAPI server will serve the static client files.

### AWS Lambda

Once a jurisdiction has defined one or more configurations, their eICR/RR data will run through a version of the Refiner that runs on AWS Lambda. Running the Refiner on AWS Lambda allows for user's files to be processed by the Refiner in an event-based way. If an RR file triggers the Lambda's execution and a configuration has been defined for a condition in that RR file, the Refiner will automatically process it and drop the resulting output into a location where the jurisdiction is able to make use of the data.

> [!IMPORTANT]
> It's important to note that, due to scalability and data privacy concerns, the AWS Lambda version of the Refiner does not directly interact with the web application's PostgreSQL database. Instead, the web application will write user-defined configurations to an AWS S3 bucket, which the Lambda then uses when processing occurs.

The Lambda is also deployed as a Docker image in production. This image is defined by [Dockerfile.lambda](./Dockerfile.lambda).

### Web App 🤝 Lambda

While the web application can be used without the Lambda, the Lambda cannot be used without the web application. The Lambda allows the Refiner to run on every incoming eICR/RR pair, however, configurations must be created by users within the web application before processing in the Lambda pipeline can occur.

Running the refining process on a pair of files can be done within the web application itself, but there is no way to run many files through it in an automated way. That's why the Lambda is a crucial component.

The web application (`refiner`) and AWS Lambda (`lambda`) Docker image builds are stored in the [dibbs-ecr-refiner GHCR repository](https://github.com/orgs/CDCgov/packages?repo_name=dibbs-ecr-refiner). When a branch is merged into `main`, both of these images will be built, tagged as `latest` and `main`, and stored here.

## Requests for Comment

For larger scale architectural changes that may need buy-in and / or comments from the rest of the eng team, we have [a standard template](docs/decisions/.template) and processed diagramed below. You can invoke the process with the command `just rfc new "Title of decision record"`. Below are some meta-rules that the team has adopted that are good to keep in mind as you go.

- RFC authors are responsible both for the architecture and splitting implementation into tickets. We’re assuming the author has the most context and thus the most ability to scope work to the appropriate size.
  - The PR’s content of the ADR should only include architecture decisions/implementation details. Any ticket writing / project management work should get handled in GitHub comments. This is to separate the “stateful” implementation information from the “stateless” project changing over time.
  - Optional, but encouraged: if any of the tickets can be worked on ahead of the ADR getting accepted / begun because it’s helpful independent of the ADR, put a note that that ticket is parallelizable!
  - Ticket writing doesn’t have to begin until after the RFC PR is merged in.
- In general, pseudocode / implementation sketches are welcome! Err on the side of more fidelity rather than less when in doubt.
  - Examples of increasing levels of “fidelity” include
    - A description of our approach in English, w/o code
    - A pseudo code / implementation sketch in GitHub comments
    - A toy implementation in a test PR - We can employ these relative to the amount of risk / ambiguity / disagreement over a part of the RCF. For example
  - You’re wanting to work through your own thoughts between two options: the level of ambiguity is medium. You can sketch out an implementation using psuedo-code.
    - There’s disagreement about the best way to do something between team members: the level of ambiguity is high. A semi-working prototype would be appropriate.
- For any database changes, sketch out the full database schema with columns, foreign keys, etc. This is to help both the reader fully understand the shape of the changes to the database schema and the author think more rigorously through the implications of changes to the schema (given the high cost of rollbacks, migrations, etc. in a live env)

## Feature building

This section will outline how to create a new feature in the eCR Refiner web application. Since the application is composed of a FastAPI server and a React frontend, we need to ensure that making requests from the client application to the server is a quick and light-weight process for developers. In order to achieve this, we use [Orval](https://orval.dev/) to generate [TanStack Query](https://tanstack.com/query/latest) React hooks. This allows developers to create a backend feature at the API level and have their client code automatically generated for them, greatly reducing the effort needed to fetch that data from the client.

More information on the code generation setup can be found in the [client package's README](./client/README.md).

### Example process

The process for building most features will follow the same process - this holds true whether you are adding, modifying, or deleting FastAPI routes.

As an example, let's say we want to give Refiner users the ability to delete their configurations. Let's walk through what the process to do this would look like.

#### Step 1: Find the appropriate file to hold the new API route

Due to the way Orval code generation works, we always want to start with implementing the backend functionality first.

Configuration management is already a part of the Refiner. We can find where `configuration` related API actions happen by navigating to [refiner/app/api/v1](/refiner/app/api/v1/) and locating [configurations.py](/refiner/app/api/v1/configurations.py). We can expect to find all of the API routing functionality within this directory. File names represent an entity and the routes within will impact that entity.

Please note that if this was the very first `configuration` related piece of functionality we were creating, the `configuration.py` would also need to be created.

#### Step 2: Add the new "delete" route

Within [configurations.py](/refiner/app/api/v1/configurations.py) we can add our new route. Since we'll be removing a configuration from the database, our route will likely look like this:

`DELETE /api/v1/configurations/:id`

Let's add the route and handler for this:

```python
# Response model to return to the client
class DeleteConfigurationResponse(BaseModel):
    id: UUID

# The FastAPI route and its async handler function
@router.delete(
    "/{configuration_id}", # ID of the configuration to delete
    response_model=DeleteConfigurationResponse, # JSON model to return to the client
    tags=["configurations"], # Tag defining which file to store the generated client code
    operation_id="deleteConfiguration", # How the hook will be named (`useDeleteConfiguration`)
)
async def delete_configuration(
    configuration_id: UUID,
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
):
    # Write the implementation
    # Get the user's jurisdiction, find the configuration by its ID, perform any validation, etc.
    ...
    ...
     # Return the response with the ID of the deleted record
    return DeleteConfigurationResponse(...)
```

We've added the ability to allow a user to delete a configuration for their jurisdiction!

To give a quick overview of what is happening above:

1. We define `DeleteConfigurationResponse` which is the response model that gets returned to the client as JSON
2. We define our route, some properties, and write up a `delete_configuration` handler that gets invoked when the client requests `DELETE api/v1/configurations/:id`
3. Once invokved, the handler code runs and returns the `DeleteConfigurationResponse`, which holds the `id` of the deleted configuration

You'll also notice that we've added a few properties to our route. We will want to include all of these properties each time we create a new route. Please refer to the [client package README `Requirements` section](./client/README.md#requirements) for more detail on each of these properties and why they are needed.

#### Step 3: Call the new route from the client app

While we worked on creating our backend functionality, Orval has been running in the background to generate our client code for us. You'll notice that `client/src/api` will contain updated files. A new hook to make use of the "delete configuration" route is now available for us to use.

As a very basic example, let's say we are going to create a `DeleteConfigButton` component that takes a `configurationId`. We will add this button to the table that lists all of a jurisdiction's configurations. Here's what that component might look like.

```tsx
// This is the generated hook that will call
// `DELETE /api/v1/configurations/:id`
import { useDeleteConfiguration } from "../../api/configurations/configurations";

// Define our button's props
interface DeleteConfigButtonProps {
  configurationId: string;
}

// Reusable button component that will delete a configuration
function DeleteConfigButton({ configurationId }: DeleteConfigButtonProps) {
  // Our TanStack Query mutation (which we've renamed to `deleteConfig` is ready for us to call)
  const { mutate: deleteConfig } = useDeleteConfiguration();

  return (
    <button
      onClick={() =>
        // As we've defined on the backend, we must pass in a configuration ID
        deleteConfig(
          { data: { configuration_id: configurationId } },
          {
            onSuccess: () => {
              console.log(`Config with ${configurationId} deleted!`);
            },
            onError: () => {
              console.log(
                `Config with ${configurationId} could not be deleted!`,
              );
            },
          },
        )
      }
    >
      Delete configuration
    </button>
  );
}
```

When this button is clicked, we will call `deleteConfig` which will invoke our new route and attempt to delete the configuration based on the ID it was provided!

#### Wrap-up

This section has provided a demonstration of the main steps to follow when creating a new feature. It's important to keep in mind that building out the backend feature first allows Orval to generate the frontend client for free, greatly reducing the overhead it would take us to have to maintain that client ourselves.

At this point, it would be worth checking out the [TanStack Query documentation](https://tanstack.com/query/latest/docs/framework/react/quick-start) to ensure you're familiar with how queries and mutations work. While we do not need to write out every query and mutation by hand, we do need to know how to make use of the TanStack Query hooks that are generated.
