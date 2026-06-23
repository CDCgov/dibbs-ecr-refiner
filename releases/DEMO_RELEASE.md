# Deploying to Demo

We have a [GitHub action](https://github.com/CDCgov/dibbs-ecr-refiner/actions/workflows/trigger_demo_workflow.yaml) to deploy to our demo environment on demand whenever a new release is ready to go out. **Doing so will cause the demo site to temporarily go down / require a manual step to get it back up, so deploy using this method only when a few seconds of downtime is acceptable.**

## Prerequisite permissions

- Access/permissions to run actions in the Skylight infra repo.
- Access to the Skylight Azure environment and the resources within the Refiner container instances / DIBBs app hub.
- Ability to run actions in the Refiner repo.
- **Double check the database schema and what the application expects match each other. If in doubt, run the migrations.**

## Instructions

1. Run the GitHub action with the desired branch / the "The event type to trigger the workflow." question set to `trigger-demo-deploy`. This will kick off the deploy action in [the Skylight infrastructure repo](https://github.com/skylight-hq/dibbs-tf-envs/actions/workflows/deploy_dibbs_services_azure_demo.yaml) that will do the deploy.
   1. Optionally, if you just want to run a plan and not kick off the full deploy, you can set the last value to `trigger-demo-plan`.
1. Watch the action run and take note of the IP address outputted at the end of the deploy job in the Skylight repo. Save this to reference in the next step.
1. Run `just cloud demo-show-network-address-pool` to verify the current IP address (optional)
1. Run `just cloud demo-update-network-address-pool
<ip_outputted_from_deploy_job>` to update the target IP address.

> [!WARNING]
> **The demo site will return a 502 Bad Gateway error until this is updated
> manually, so only run the deploy job if the downtime won't cause trouble**

The demo site should be updated from there! If you want to double check, the application commit hash is displayed at the bottom of the footer, which you can compare against the latest commit in main.
