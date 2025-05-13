# API Layer

## Overview

This directory contains the API routes, endpoint definitions, and middleware components for the application.

### Structure

```
api/
├── middleware/
│   └── spa.py        # SPA fallback middleware
└── v1/
    ├── demo.py       # Demo endpoints
    ├── ecr.py        # eCR processing endpoints
    ├── file_io.py    # File handling endpoints
    └── v1_router.py  # Route aggregation
```

## Components

### Endpoints

API endpoints are organized by version and functionality:
- `demo.py`: Demo endpoints for testing and examples
- `ecr.py`: Electronic Case Reporting (eCR) processing endpoints
- `file_io.py`: File handling and processing endpoints
- `v1_router.py`: Route aggregation for v1 API

### Middleware

Custom middleware components that modify request/response behavior:
- `spa.py`: Fallback middleware for Single Page Application (SPA) routing, serving index.html for client-side routes

## Versioning

API endpoints are versioned using directory structure (v1, v2, etc.) for clear separation and maintenance.

## Documentation

All endpoints are documented using FastAPI's built-in OpenAPI support. View the complete API documentation at `/docs` or `/redoc`.
