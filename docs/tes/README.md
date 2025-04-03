# TES

## Web based interface

### Specification category

> [!NOTE] 
> **Specification category**: This server currently contains released eRSD and TES data bundles. They both contain very similar data, but are grouped/organized in different ways. The eRSD groups data by "triggering categories" (e.g. medications, lab orders) that are maintained by RCKMS to generate electronic initial case reports for tracked health conditions. TES data bundles are grouped by overarching "condition categories" (e.g. influenza, mpox)

### Release version

> [!NOTE]
> **Release version**: All released (final) TES and eRSD bundles are given a unique version. Released bundles can no longer be edited, apart from small changes to the metadata.

### Grouping Level

> [!NOTE]
> **Grouping Level**: Some bundles may have the ability to be viewed with narrower or wider content focus. Changing the grouping level helps you to view the data from different perspectives. eRSD bundles can only be viewed from the context of a "triggering category."

### Available groupers

> [!NOTE]
> **Available groupers**: Code expansions below will be performed at the grouper level. A grouper may be one Value Set, or may contain other Value Sets.

### Results

Let's say we pick **Anthrax** as the grouper. This is what gets returned:

|Field|Value|
|---|---|
|Title|Anthrax|
|Computable Name|Anthrax|
|Steward|CSTE Steward|
|Publisher|Association of Public Health Laboratories (APHL)|
|Description|The set of all codes from value sets used in Reporting Specifications that are associated with the 'Anthrax' condition.|
|URL|`https://tes.tools.aimsplatform.org/api/fhir/ValueSet/cee10ec6-5f3c-42c8-91af-5bc3f4ab2daf`|
|Version|`1.0.0`|

It will also contain **Value Sets**

In this case only one is returned:

|Title|URL|Date|Version|
|---|---|---|---|
|Anthrax|`https://tes.tools.aimsplatform.org/api/fhir/ValueSet/rs-grouper-409498004`|October 8, 2024|`20241008`|

You can click to expand for **Codes** and the expansion will be listed as generated on the date that the request is made:

|Display|Code|System|System Version|
|---|---|---|---|
|Abdominal colic (finding)|`9991008`|`http://snomed.info/sct`|No Version|
|Abdominal colic in adult or child greater than 12 months (finding)|`137891000119105`|`http://snomed.info/sct`|No Version|
|Abdominal colic in child less than or equal to 12 months (finding)|`136051000119105`|`http://snomed.info/sct`|No Version|
|Abdominal discomfort (finding)|`43364001`|`http://snomed.info/sct`|No Version|
|Abdominal muscle pain (finding)|`28221000119103`|`http://snomed.info/sct`|No Version|
|Abdominal pain - cause unknown (finding)|`314212008`|`http://snomed.info/sct`|No Version|
|Abdominal pain (finding)|`21522001`|`http://snomed.info/sct`|No Version|
|Abdominal pain through to back (finding)|`74704000`|`http://snomed.info/sct`|No Version|
|Abdominal pain worse on motion (finding)|`71850005`|`http://snomed.info/sct`|No Version|
|Abdominal tenderness (finding)|`43478001`|`http://snomed.info/sct`|No Version|
|Abdominal wall pain (finding)|`162042000`|`http://snomed.info/sct`|No Version|
|Abdominal wind pain (finding)|`45979003`|`http://snomed.info/sct`|No Version|
|Abnormal (qualifier value)|`263654008`|`http://snomed.info/sct`|No Version|
|Abnormal presence of (qualifier value)|`43261007`|`http://snomed.info/sct`|No Version|
|Abnormal result (qualifier value)|`280415008`|`http://snomed.info/sct`|No Version|
|Absent minded (finding)|`46991000`|`http://snomed.info/sct`|No Version|
|Aching headache (finding)|`162307009`|`http://snomed.info/sct`|No Version|
|Acute abdomen (disorder)|`9209005`|`http://snomed.info/sct`|No Version|
|Acute abdominal pain (finding)|`116290004`|`http://snomed.info/sct`|No Version|
|Acute bacterial pharyngitis (disorder)|`195658003`|`http://snomed.info/sct`|No Version|
|Acute confusion (finding)|`130987000`|`http://snomed.info/sct`|No Version|
|Acute exacerbation of chronic abdominal pain (finding)|`444746004`|`http://snomed.info/sct`|No Version|
|Acute headache (finding)|`735938006`|`http://snomed.info/sct`|No Version|
|Acute laryngopharyngitis (disorder)|`55355000`|`http://snomed.info/sct`|No Version|
|Acute pharyngitis (disorder)|`363746003`|`http://snomed.info/sct`|No Version|
|Acute phlegmonous pharyngitis (disorder)|`195656004`|`http://snomed.info/sct`|No Version|
|Acute rise of fever (finding)|`271749004`|`http://snomed.info/sct`|No Version|
|Acute ulcerative pharyngitis (disorder)|`195657008`|`http://snomed.info/sct`|No Version|
|Acute viral pharyngitis (disorder)|`195662009`|`http://snomed.info/sct`|No Version|
|Acute vomiting (disorder)|`23971007`|`http://snomed.info/sct`|No Version|
|Added respiratory sounds (finding)|`53972003`|`http://snomed.info/sct`|No Version|
|Altered mental status (finding)|`419284004`|`http://snomed.info/sct`|No Version|
|Ankle edema (finding)|`26237000`|`http://snomed.info/sct`|No Version|
|Anthrax (disorder)|`409498004`|`http://snomed.info/sct`|No Version|
|Anthrax manifestation (disorder)|`111800004`|`http://snomed.info/sct`|No Version|
|Anthrax pneumonia (disorder)|`195902009`|`http://snomed.info/sct`|No Version|

There are 1000 rows of results.

## From the docs

### Condition Grouper

A **Condition Grouper** is a grouping ValueSet that contains Reporting Specification Groupers that typically share the same overarching condition.

For instance, an influenza condition grouper may contain two reporting specification groupers: one a more general ValueSet addressing the Influenza condition, and another related to Influenza Associated Hospitalization condition. 

Condition Groupers themselves do not have an explicit association with a specific condition code, unlike their contents (Reporting Specification Groupers).

### Reporting Specification Grouper

A Reporting Specification Grouper is a ValueSet with a definition and expansion that contains the codes from all of the ValueSets used in reporting specification implementations that are associated with a particular condition code.

These ValueSets have an explicit association with a condition code - a ‘clinical focus’ useContext.

For instance, an influenza condition reporting specification grouper may contain all condition codes related to SNOMED code `43692000` `"[Influenzal acute upper respiratory infection (disorder)]"`, while an influenza hospitalization reporting specification grouper may be based on a different SNOMED code, such as SNOMED `719590007` `"[Influenza caused by seasonal influenza virus (disorder)]"`

> [!TIP]
> A _reporting specification grouper_ can be expanded by invoking the `$expand` operation on the instance.

## TES API

The API for the TES is a FHIR server that supports standard FHIR REST and FHIR Search functionality. The API is protected by API Key-based authentication and authorization. 

- FHIR Endpoints
  - Production – `https://tes.tools.aimsplatform.org/api/fhir`
- API Key Authentication
  - Users can generate an API key from within the TES application. The API Key should be included as an `X-API-KEY` header in requests that are submitted to the application.
- API Key Authorization
  - The TES currently defines the following roles: 
    - Viewer
    - Publisher
    - Admin 
  - All three will have full read access. Only publishers and admins will be able to publish new content to the repository.

### CapabilityStatment

The CapabilityStatment can be obtained by hitting the `/metadata` endpoint on the TES api. This has been saved as a `.json` file to make it easier to search through. To make it easier, here are some `jq` commands to find specific pieces of info:

#### `jq` commands:

```bash
jq '.rest[].resource[] | select(.type=="ValueSet") | .searchParam[]' tes-CapabilityStatement.json
```

### `.http` file examples

To use the `.http` file with example requests to the TES API you'll need to create an `http-client.env.json` file (or other kind of `.env` file for the API key to be added to the header of the requests). The contents should look something like this:

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

