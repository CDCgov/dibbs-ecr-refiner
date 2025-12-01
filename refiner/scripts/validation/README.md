# Validation of eCR Data

This directory contains all assets required for validating Clinical Document Architecture (CDA) documents against their official HL7 standards. This includes the source Schematron (`.sch`) files, their required Vocabulary (`.xml`) dependencies, the generated XSLT (`.xslt`) artifacts, and the tooling used to create them.

The goal is to provide a clear, automated, and maintainable system for ensuring our test data conforms to the correct specifications.

## Workflow Overview

The validation process follows three main steps:

1. **Acquire Source Files**: The raw Schematron (`.sch`) and Vocabulary (`.xml`) files are downloaded from their official HL7 source repositories and placed into the appropriate standard-specific directory. This is currently a manual process but is designed to be automated.
2. **Generate Artifacts**: The `generate_xslt_from_sch.py` script is run to compile the `.sch` files into executable `.xslt` artifacts. This step only needs to be re-run when the source `.sch` files are updated.
3. **Validate Documents**: The `validate_source_data.py` script is used to run the compiled `.xslt` artifacts against an eICR or RR document, providing an interactive way to check for validation errors.

## Directory and Naming Convention

The subdirectories are organized using a consistent naming convention:

**`[standard]-[technology]-[version]`**

- **`standard`**: The acronym for the standard (e.g., `eicr`, `rr`).
- **`technology`**: The base technology used (e.g., `cda`).
- **`version`**: The official "Standard for Trial Use" (STU) version number.

This convention ensures that assets are grouped logically and provides clear traceability to the source specification.

## Standards and Source Repositories

Each directory contains the canonical `.sch` source file, its corresponding compiled `.xslt` artifact, and any required vocabulary files.

### Vocabulary Files (`voc.xml` or `_VOCABULARY.xml`)

The Schematron rules depend on external XML files that contain value sets and code systems. These "vocabulary" files are required for validation and must be kept in the same directory as the `.sch` file that references them.

### `eicr-cda-stu-1.1.1/`

- **Standard**: Public Health Case Report (eCR), STU 1.1.1
- **Source Repository**: [HL7/CDA-phcaserpt-1.1.1](https://github.com/HL7/CDA-phcaserpt-1.1.1)

### `eicr-cda-stu-3.0/`

- **Standard**: electronic Initial Case Report (eICR), STU 3.0
- **Source Repository**: [HL7/CDA-phcaserpt-1.3.0](https://github.com/HL7/CDA-phcaserpt-1.3.0)

> [!IMPORTANT]
> The repository name `1.3.0` is an internal version; the official standard version is STU 3.0.

### `eicr-cda-stu-3.1.1/`

- **Standard**: electronic Initial Case Report (eICR), STU 3.1.1
- **Source Repository**: [HL7/CDA-phcaserpt](https://github.com/HL7/CDA-phcaserpt)

### `rr-cda-stu-1.1.0/`

- **Standard**: Reportability Response (RR), STU 1.1.0
- **Source Repository**: [HL7/CDA-phcr-rr-1.1.0](https://github.com/HL7/CDA-phcr-rr-1.1.0)

## Tooling and Usage

This directory contains the core engine and two primary Python scripts for managing and running validation.

### `schxslt/` - The Schematron Engine

This directory contains the **SchXslt** library, which is a modern XSLT-based implementation of Schematron. It provides the core stylesheets that power the compilation of our `.sch` rule files into executable `.xslt` artifacts. It should be treated as a third-party dependency.

### `generate_xslt_from_sch.py` - Compiling Artifacts

This script finds all Schematron (`.sch`) files in the subdirectories and compiles them into XSLT (`.xslt`) artifacts using the `schxslt` engine. The generated `.xslt` files are the "compiled" assets that the validation script uses.

**When to Run:** You only need to run this script if you have updated or added new `.sch` files.

**How to Run:**

```bash
python validation/generate_xslt_from_sch.py
```

### `validate_source_data.py` - Validating Documents

This is the main interactive script for validating a single eICR or RR document. It automatically detects the standard and version of the selected XML file and runs the appropriate validation artifact against it.

**Dependency:** This script uses `fzf` to provide an interactive file selection menu. You must have `fzf` installed and available in your path.

**How to Run:**

```bash
python validation/validate_source_data.py
```

The script will open an `fzf` prompt, allowing you to select an XML file from the `refiner/scripts/data/source-ecr-files/` directory to validate.

## Automation

> [!WARNING]
> This hasn't been completed yet and is a to-do action for later.

The `.sch` and `voc.xml` files in this directory are intended to be kept in sync with their source HL7 repositories. A scheduled GitHub Action (cron job) will be implemented to periodically check for updates, pull down the latest files, and open a Pull Request with any changes. This automates the maintenance of our validation assets and ensures they do not become stale.
