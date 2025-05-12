# Core Layer

## Overview

Contains core application components, models, and base configurations.

### Structure

```
core/
├── app/
│   ├── base.py      # Base service configuration
│   └── openapi.py   # Custom OpenAPI configuration
├── models/
│   ├── api.py       # API models and schemas
│   └── types.py     # Core type definitions
└── exceptions.py    # Exception hierarchy
```

## Configuration

Base application configuration and OpenAPI customization live here, centralizing core setup and documentation requirements.

## Models

Defines data structures and type definitions used throughout the application using Pydantic models and Python built-in type hints.
