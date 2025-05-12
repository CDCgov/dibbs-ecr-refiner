# API Layer

## Overview

This directory contains the API routes and endpoint definitions for the application.

### Structure

```
api/
└── v1/
    ├── demo.py       # Demo endpoints
    ├── ecr.py        # eCR processing endpoints
    ├── file_io.py    # File handling endpoints
    └── v1_router.py  # Route aggregation
```

## Versioning

API endpoints are versioned using directory structure (v1, v2, etc.) for clear separation and maintenance.

## Documentation

All endpoints are documented using FastAPI's built-in OpenAPI support. View the complete API documentation at `/docs` or `/redoc`.
