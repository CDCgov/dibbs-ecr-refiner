# 9. Normalizing Storage of Codes

Date: 2026-04-17

## Status

Proposed

## Context and Problem Statement

Following a Slack discussion about implementation of [1099](https://app.zenhub.com/workspaces/dibbs-ecr-refiner-67ddd053d70b9f000ffbb542/issues/gh/cdcgov/dibbs-ecr-refiner/1099), it was determined that this feature may be a chance to implement a long-desired refactor of the schema we're using to store codesets within the application. Several forthcoming features will need to retreive this data more granularly than the current storage schema easily allows, and the engineering team has acknowledged for a while that this area of the codebase has needed refactoring.

The current decision to store codes as JSONB was made when the Refiner was a much different application, where codesets reads from the database were the optimized operation, while writes / updates were deprioritized. With the evolution of the lambda, application update operations following the TES, and the development of current and upcoming web app features, this storage decision is in need of revisiting.

Below are several decision drivers that will inform our decision of 1. Whether / how to refactor our schema to better support codeset information and 2. How to roll out the proposed refactor across the relevant modules of the codebase

## Decision Drivers

- Support future application development while maintaining current application functionality / validation around codeset information.
- Allow for dynamic retreival of codeset information, including the code itself and useful metadata (display name, code system, TES version membership, etc.)
- Leverage the relational benefits of Postgres. Avoid unnecessary JSONB.
- Minimize the necessary refactoring needed across seeding, retreival, rendering, and other necessary application functions while maximizing storage flexibility and maintainbility of codeset storage as needed for current and future feature work.
- Make the engineering team feeling good about the way codes are stored. Does it spark joy?

## Considered Options

- Storage of codes with a direct foreign-key into configurations
- Deduplicated storage of codes with a composite system / code key, with joins into configurations
- Do nothing, store more JSON

## Decision Outcome

### Proposed Schema

## Appendix (OPTIONAL)

Add any links here that are relevant for understanding your proposal or its background.

**Be sure to read the information about this in [CONTRIBUTING](https://github.com/CDCgov/dibbs-ecr-refiner/blob/main/CONTRIBUTING.md##Request-for-comment)**
