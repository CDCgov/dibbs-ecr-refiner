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

## Appendix

> [!NOTE]
> `lxml` XML element types in this codebase
>
> When working with XML in Python using `lxml`, you will see both `_Element` and `etree.Element` in our code.

- **Type hints:** We use `_Element` (from `lxml.etree`) for type annotations, because it is the actual type of XML element objects. This is important for static analysis and tools.
- **Element construction:** We use `etree.Element(...)` in the code to create elements. This is a factory function that returns an `_Element` instance.

**Why?**

- `etree.Element` is *not* a class, but a function. Using it as a type hint is incorrect and may confuse type checkers.
- `_Element` is the correct type for variables that hold XML elements.

See also: [lxml _Element API docs](https://lxml.de/api/lxml.etree._Element-class.html)

This pattern will change in `lxml` 6.0; check the [PR](https://github.com/lxml/lxml/pull/405) for more information.
