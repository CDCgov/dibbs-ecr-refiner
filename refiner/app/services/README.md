# Services Layer

## Overview

Contains the business logic implementation for the application.

### Structure

```
services/
├── db.py            # Database service
├── file_io.py       # File processing logic
├── refine.py        # XML refinement logic
└── terminology.py   # Clinical terminology services
```

## Service Components

- **Database**: Handles the querying and unpacking of data
- **File I/O**: Handles file uploads, XML parsing, and ZIP processing
- **Refine**: Implements core XML document refinement logic
- **Terminology**: Manages clinical terminology and code systems

## Configuration

Services use configuration from JSON assets in the project root for processing rules and validation.
