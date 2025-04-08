# Terminology Exchange Service (TES) API Integration Guide

## Background

The Terminology Exchange Service (TES) reduces the burden of terminology management for public health agencies (PHAs) by providing centralized, condition-associated codes through a searchable user interface and an application programming interface (API). These codes are curated from the Reportable Conditions Knowledge Management System (RCKMS) value sets and the Electronic Reporting and Surveillance Distribution (eRSD) system.

There are several challenges that make it more difficult for PHAs to leverage electronic case reporting (eCR) terminology, including:
- Identifying condition-indicating codes within Electronic Initial Case Reports (eICR)
- Understanding codes that offer contextual information surrounding reported conditions
- Addressing narrative descriptor gaps in coded data elements
- Managing and maintaining vocabularies
- Utilizing coded values for ingestion and integration into surveillance systems

The TES aims to support PHAs to process, ingest, and utilize eCR data more efficiently and effectively through improved terminology management.

## Benefits of the TES

- Streamlines vocabulary management and reduces duplication of efforts across PHAs by providing relevant, curated, and centralized codes.
- Helps identify and contextualize conditions through curated value sets to ensure data are useful and actionable for public health.
- Informs users of content and value set updates with narrative description look-ups for value sets captured within the tool.

## Organization of Terminology

The TES FHIR server provides terminology services that organize medical terminology (primarily SNOMED CT codes) in two ways:

1. **Triggering categories (eRSD)**: Grouped by types of clinical events (medications, lab orders, etc.)
2. **Condition categories (TES)**: Grouped by health conditions (influenza, anthrax, etc.)

> [!NOTE] 
> **Specification category**: This server currently contains released eRSD and TES data bundles. They both contain very similar data, but are grouped/organized in different ways. The eRSD groups data by "triggering categories" that are maintained by RCKMS to generate electronic initial case reports for tracked health conditions. TES data bundles are grouped by overarching "condition categories".

### Content Structure

The TES uses two primary types of ValueSets to organize terminology:

#### Condition Grouper

A **Condition Grouper** is a grouping ValueSet that contains Reporting Specification Groupers that typically share the same overarching condition.

For instance, an influenza condition grouper may contain two reporting specification groupers: one a more general ValueSet addressing the Influenza condition, and another related to Influenza Associated Hospitalization condition. 

Condition Groupers themselves do not have an explicit association with a specific condition code, unlike their contents (Reporting Specification Groupers).

#### Reporting Specification Grouper

A **Reporting Specification Grouper** is a ValueSet with a definition and expansion that contains the codes from all of the ValueSets used in reporting specification implementations that are associated with a particular condition code.

These ValueSets have an explicit association with a condition code - a 'clinical focus' useContext.

For instance, an influenza condition reporting specification grouper may contain all condition codes related to SNOMED code `43692000` `"[Influenzal acute upper respiratory infection (disorder)]"`, while an influenza hospitalization reporting specification grouper may be based on a different SNOMED code, such as SNOMED `719590007` `"[Influenza caused by seasonal influenza virus (disorder)]"`.

> [!TIP]
> A reporting specification grouper can be expanded by invoking the `$expand` operation on the instance.

## TES API Overview

The Application Programming Interface (API) for the Terminology Exchange Service (TES) is a FHIR server that supports standard FHIR REST and FHIR Search functionality built on top of HAPI 7.2. The API is protected by API Key-based authentication and authorization.

### FHIR Endpoints

- Production – `https://tes.tools.aimsplatform.org/api/fhir`

### API Key Authentication

Users can generate an API key from within the TES application. The API Key should be included as an `X-API-KEY` header in requests that are submitted to the application.

### API Key Authorization

The TES currently defines the following roles:
- **Viewer**: Read-only access
- **Publisher**: Read access and ability to publish new content
- **Admin**: Full read access and ability to publish new content

All three roles have full read access. Only publishers and admins can publish new content to the repository.

## Getting Started with the API

### 1. Basic Setup

```python
import requests

API_URL = "https://tes.tools.aimsplatform.org/api/fhir"
API_KEY = "your_api_key_here"

headers = {
    "X-API-KEY": API_KEY,
    "Accept": "application/json"
}

def make_tes_request(url_suffix, params=None):
    """Helper function for TES API requests"""
    try:
        response = requests.get(
            f"{API_URL}{url_suffix}",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None
```

### Search Patterns

#### 1. Get Active ValueSets

```python
def get_active_valuesets():
    """Get all active ValueSets"""
    params = {"status": "active"}
    return make_tes_request("/ValueSet", params)

active_vs = get_active_valuesets()
if active_vs:
    print(f"Found {active_vs.get('total', 0)} active ValueSets")  # Returns 20+ in production
```

#### 2. Search by Contained Code

```python
def find_valuesets_by_code(code, code_system=None):
    """Find ValueSets containing a specific code"""
    params = {"code": code}
    if code_system:
        params["system"] = code_system
    return make_tes_request("/ValueSet", params)

# example: find ValueSets containing SNOMED code for Abdominal colic (9991008)
abdominal_colic_vs = find_valuesets_by_code("9991008")  
if abdominal_colic_vs:
    print(f"Found {len(abdominal_colic_vs.get('entry', []))} ValueSets containing code 9991008")
```

#### 3. Search by Condition (SNOMED Context)

```python
def find_valuesets_by_condition(snomed_code):
    """Find ValueSets associated with a condition"""
    params = {"context": f"http://snomed.info/sct|{snomed_code}"}
    return make_tes_request("/ValueSet", params)

# example: find Hepatitis B (66071002) ValueSets
hepatitis_b_vs = find_valuesets_by_condition("66071002")  
if hepatitis_b_vs:
    print(f"Found {hepatitis_b_vs.get('total', 0)} Hepatitis B ValueSets")  # Returns 12 in production
```

#### 4. Search by Title/Description

```python
def search_valuesets_by_text(field, text, status=None):
    """Search by title or description"""
    params = {field: text}
    if status:
        params["status"] = status
    return make_tes_request("/ValueSet", params)

# title search for active ValueSets
flu_title_vs = search_valuesets_by_text("title", "Influenza", "active")

# description search
poisoning_vs = search_valuesets_by_text("description", "poisoning")  # Returns 15+ for "Influenza"
```

#### 5. Find ValueSets from Specific CodeSystem

```python
def find_valuesets_by_codesystem(system_url):
    """Find ValueSets using codes from a specific system"""
    params = {"reference": system_url}
    return make_tes_request("/ValueSet", params)

# example: find all ValueSets using LOINC codes
loinc_vs = find_valuesets_by_codesystem("http://loinc.org")  # Returns 20+ in production
```

#### 6. Pagination with `_count`

```python
def get_paginated_valuesets(page_size=20, page=1):
    """Get paginated ValueSet results"""
    params = {
        "_count": page_size,
        "_getpagesoffset": (page - 1) * page_size
    }
    return make_tes_request("/ValueSet", params)

# get first 5 ValueSets
first_page = get_paginated_valuesets(page_size=5)
```

#### 7. ValueSet Operations

```python
def expand_valueset(valueset_id):
    """Expand a ValueSet to see all codes"""
    return make_tes_request(f"/ValueSet/{valueset_id}/$expand")

def validate_code(valueset_id, code, system):
    """Check if a code is in a ValueSet"""
    params = {"code": code, "system": system}
    return make_tes_request(f"/ValueSet/{valueset_id}/$validate-code", params)

# example usage with real IDs from search results:
# expand a ValueSet
flu_codes = expand_valueset("rs-grouper-6142004")  # Returns pre-calculated expansion

# validate a code
validation = validate_code(
    # Hepatitis B ValueSet
    "rs-grouper-66071002",
    "active",
    "urn:oid:2.16.840.1.113883.3.1937.98.5.8"
)
```

> [!NOTE]
> See the [`explore-tes.py`](explore-tes.py) to run the different examples and see the responses.

## Understanding Healthcare Terminology Systems

TES works with multiple standard healthcare terminology systems. Here's a brief overview of the main ones:

### SNOMED CT

**SNOMED Clinical Terms** is a comprehensive clinical terminology system used for the electronic exchange of clinical health information. It provides a standardized vocabulary for clinical documentation and reporting.

Example SNOMED code: `66071002` - "Hepatitis B" 

### LOINC

**Logical Observation Identifiers Names and Codes** is a database and universal standard for identifying medical laboratory observations. It is primarily used for laboratory test orders and results.

Example LOINC code: `94500-6` - "SARS-CoV-2 (COVID-19) RNA [Presence] in Respiratory specimen by NAA with probe detection"

### RxNorm

**RxNorm** provides normalized names for clinical drugs and links to many of the drug vocabularies commonly used in pharmacy management and drug interaction software.

Example RxNorm code: `1000001` - "Acetaminophen 325 MG Oral Tablet"

### ICD-10-CM

**International Classification of Diseases, 10th Revision, Clinical Modification** is a system used by physicians and other healthcare providers to classify and code diagnoses, symptoms, and procedures.

Example ICD-10-CM code: `A22.9` - "Anthrax, unspecified"

### ICD-9-CM

The older version of ICD that is still used in some contexts for historical data.

Example ICD-9-CM code: `022.9` - "Anthrax, unspecified"

## Development Setup

### Working with HTTP Examples

To use the provided `.http` file examples with the TES API, you can use tools like:

- [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) on VS Code
- [Kulala.nvim](https://github.com/mistweaverco/kulala.nvim) on Neovim

#### For REST Client

You can read about adding environment variables [here](https://marketplace.visualstudio.com/items?itemName=humao.rest-client#environment-variables); and below for a sample settings file:

```json
"rest-client.environmentVariables": {
    "$shared": {
        "version": "v1",
        "prodToken": "foo",
        "nonProdToken": "bar"
    },
    "local": {
        "version": "v2",
        "host": "localhost",
        "token": "{{$shared nonProdToken}}",
        "secretKey": "devSecret"
    },
    "production": {
        "host": "example.com",
        "token": "{{$shared prodToken}}",
        "secretKey" : "prodSecret"
    }
}
```

#### For `kulala.nvim`:

create an `http-client.env.json` file with the following structure:

```json
{
  "$schema": "https://raw.githubusercontent.com/mistweaverco/kulala.nvim/main/schemas/http-client.env.schema.json",
  "$shared": {
    "$default_headers": {
      "Content-Type": "application/json",
      "Accept": "application/json"
    }
  },
  "dev": {
    "API_URL": "https://tes.tools.aimsplatform.org/api/fhir",
    "API_KEY": "your-api-key"
  }
}
```

> [!NOTE]
> These are just two examples and there may be others based on the development tools that you use for `.http` files.

### Working with the python examples

To use the provided python examples with the TES API, create a `.env` file with the following structure:

```
TES_API_URL="https://tes.tools.aimsplatform.org/api/fhir"
TES_API_KEY="your-api-key"
```

> [!NOTE]
> the `requirements.txt` is associated with the [`explore-tes.py`](explore-tes.py) file, so please make sure you run `pip install -r requirements.txt` prior to running the script.

### Exploring the entire API Capabilities

You can obtain the complete CapabilityStatement by requesting the `/metadata` endpoint.

There is a saved version of this response here [`tes-CapabilityStatement.json`](tes-CapabilityStatement.json) that you can view or slice by using tools like `jq` to extract specific parts of it:

```bash
jq '.rest[].resource[] | select(.type=="ValueSet") | .searchParam[]' tes-CapabilityStatement.json
```

