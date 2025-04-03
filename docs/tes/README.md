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

### Authentication Setup

To use the TES API, you'll need to include your API key in the `X-API-KEY` header of every request:

```python
import requests

API_URL = "https://tes.tools.aimsplatform.org/api/fhir"
API_KEY = "your-api-key"  # Replace with your actual API key

headers = {
    "X-API-KEY": API_KEY,
    "Accept": "application/json"
}

# example request to get the FHIR CapabilityStatement
response = requests.get(f"{API_URL}/metadata", headers=headers)
capability_statement = response.json()
```

### Common API requests

Here are examples of common API requests to retrieve ValueSets from the TES:

1. Get active ValueSets

```python
# get all active value sets
response = requests.get(f"{API_URL}/ValueSet?status=active", headers=headers)
active_value_sets = response.json()
```

2. Search by ValueSet code

```python
# get ValueSet by specific code
code = "9991008"
response = requests.get(f"{API_URL}/ValueSet?code={code}", headers=headers)
value_sets_with_code = response.json()
```

3. Search by condition (using SNOMED CT context)

```python
# get ValueSets by SNOMED condition code (Hepatitis B - 66071002)
snomed_code = "66071002"
response = requests.get(f"{API_URL}/ValueSet?context=http://snomed.info/sct|{snomed_code}", headers=headers)
condition_value_sets = response.json()
```

4. Search by title or description

```python
# search by title
title = "Hepatitis B"
response = requests.get(f"{API_URL}/ValueSet?title={title}&status=active", headers=headers)
hepatitis_b_value_sets = response.json()

# search by description containing "Influenza"
description = "Influenza"
response = requests.get(f"{API_URL}/ValueSet?description={description}", headers=headers)
influenza_value_sets = response.json()
```

### Example Response Structure

Responses are FHIR bundles, for example; if we search by description containing "Influenza" (from the example above), we receive this FHIR bundle as a response:

```json
{
  "resourceType": "Bundle",
  "id": "c0559580-6ed6-4f3a-934e-0ad5e08f0a35",
  "meta": {
    "lastUpdated": "2025-04-03T18:30:34.495+00:00"
  },
  "type": "searchset",
  "total": 15,
  "link": [
    {
      "relation": "self",
      "url": "https://tes.tools.aimsplatform.org/api/fhir/ValueSet?description=Influenza"
    }
  ],
  "entry": [
    {
      "fullUrl": "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/2.16.840.1.113762.1.4.1146.133",
      "resource": {
        "resourceType": "ValueSet",
        "id": "2.16.840.1.113762.1.4.1146.133",
        "meta": {
          "versionId": "1",
          "lastUpdated": "2024-11-06T18:52:04.343+00:00",
          "source": "#KwfuvchZ8Shkxhiw",
          "profile": [
            "http://hl7.org/fhir/us/ecr/StructureDefinition/us-ph-triggering-valueset"
          ]
        },
        "extension": [
          {
            "url": "http://hl7.org/fhir/StructureDefinition/valueset-author",
            "valueContactDetail": {
              "name": "CSTE Author"
            }
          },
          {
            "url": "http://hl7.org/fhir/StructureDefinition/valueset-steward",
            "valueContactDetail": {
              "name": "CSTE Steward"
            }
          }
        ],
        "url": "http://cts.nlm.nih.gov/fhir/ValueSet/2.16.840.1.113762.1.4.1146.133",
        "identifier": [
          {
            "system": "urn:ietf:rfc:3986",
            "value": "urn:oid:2.16.840.1.113762.1.4.1146.133"
          }
        ],
        "name": "InfluenzaDisordersICD10CM",
        "title": "Influenza (Disorders) (ICD10CM)",
        "status": "active",
        "experimental": false,
        "publisher": "CSTE Steward",
        "description": "Influenza (Disorders) (ICD10CM)",
        "useContext": [
          {
            "code": {
              "system": "http://terminology.hl7.org/CodeSystem/usage-context-type",
              "code": "focus"
            },
            "valueCodeableConcept": {
              "coding": [
                {
                  "system": "http://snomed.info/sct",
                  "code": "661761000124109"
                }
              ],
              "text": "Death associated with influenza (event)"
            }
          },
          {
            "code": {
              "system": "http://hl7.org/fhir/us/ecr/CodeSystem/us-ph-usage-context-type",
              "code": "priority"
            },
            "valueCodeableConcept": {
              "coding": [
                {
                  "system": "http://hl7.org/fhir/us/ecr/CodeSystem/us-ph-usage-context",
                  "code": "emergent"
                }
              ],
              "text": "Emergent"
            }
          },
          {
            "code": {
              "system": "http://terminology.hl7.org/CodeSystem/usage-context-type",
              "code": "focus"
            },
            "valueCodeableConcept": {
              "coding": [
                {
                  "system": "http://snomed.info/sct",
                  "code": "6142004"
                }
              ],
              "text": "Influenza (disorder)"
            }
          },
          {
            "code": {
              "system": "http://hl7.org/fhir/us/ecr/CodeSystem/us-ph-usage-context-type",
              "code": "priority"
            },
            "valueCodeableConcept": {
              "coding": [
                {
                  "system": "http://hl7.org/fhir/us/ecr/CodeSystem/us-ph-usage-context",
                  "code": "emergent"
                }
              ],
              "text": "Emergent"
            }
          },
          ...
```

The FHIR bundles can be very large so this is just part of the response.

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

To use the provided `.http` file examples with the TES API, create an `http-client.env.json`` file with the following structure:

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
> the `"$schema"` value is for using the Kulala NeoVim package. There are likely other `.env` examples if you are using a different tool for `.http` files.

### Exploring the API Capabilities

You can obtain the complete CapabilityStatement by requesting the `/metadata` endpoint:

```python
response = requests.get(f"{API_URL}/metadata", headers=headers)
capability_statement = response.json()
```

There is a saved version named `tes-CapabilityStatement.json` that you can explore by opening the file or using tools like `jq` to extract parts of it:

```bash
jq '.rest[].resource[] | select(.type=="ValueSet") | .searchParam[]' tes-CapabilityStatement.json
```

