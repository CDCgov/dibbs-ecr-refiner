# 6. displayName Enrichment and Better Search

Date: 2026-03-07

## Status

Proposed

## Context and Problem Statement

Historically, our eICR and RR refinement process has relied on brittle, code-centric XPath search patterns. This has caused a lack of clinical context, poor section conformity to the HL7 IG, and narrative tables that do not accurately represent the structured data or clinical meaning. We also have not yet implemented the `displayName` enrichment fix from the 00005 decision file.

Additionally, terminology objects currently store codes as a flat set and often include embedded XPaths or context that are not reusable or maintainable. Section and entry processing instructions lack clear separation for structured entries vs. narrative text generation—limiting our ability to meet IG requirements and to support robust narrative reconstruction and enrichment.

As our needs grow to produce jurisdiction-ready eICRs, comply with IG 3.1.1 constraints, and support more robust and testable enrichment—we must move to a model-driven, section-aware approach. This means enriching `displayNames` as we extract data, organizing section-specific logic, and generating `<text>` narrative tables using strong clinical models.

## Decision Drivers

- **Clinical Integrity:** Narratives and structured entries must match and reflect complete, contextually correct clinical data.
- **Maintainability:** Section-specific, model-driven parsing is easier to maintain and expand than brittle union XPath code.
- **IG Conformance:** Extraction and table generation must be per IG constraints (code systems, templates, narrative structure).
- **Performance:** Entry-by-entry parsing avoids large XPath evaluations and improves clarity/reliability.
- **Incremental Rollout:** Allow starting with core sections for refined `<text>` generation, e.g. Results, Problems, Medications, Immunizations; expanding over time.
- **Future-Proofing:** Enables easier jurisdictional customization and richer narrative features down the line.
- **Terminology Flexibility:** Robust support for code system granularity and context-specific matching, decoupling XPaths from terminology data.

## Considered Options

### 1. Post-processing displayName enrichment

- **Pros:** Simple, quick to implement as a final XML pass.
- **Cons:** Context-agnostic; doesn’t improve narrative generation, risks mismatch between narrative and entries.

### 2. Global parsing fix-up (lxml events)

- **Pros:** Fully decouples enrichment from refinement logic.
- **Cons:** High complexity; difficult to debug and maintain. Not targeted to clinical sections.

### 3. Union XPath code search

- **Pros:** Easy for initial implementation.
- **Cons:** Brittle, misses organizer/panel context; not maintainable or IG-conformant.

### 4. Model-driven, section-specific extraction and enrichment (**Chosen**)

- **Pros:** Robust, IG-conformant, maintainable; enables displayName enrichment and strong narrative reconstruction; supports sectional code system filtering and entry-by-entry logic; avoids sibling pruning errors and table mismatches. Decouples code storage from XPaths and allows flexible matching per entry and per section.
- **Cons:** Requires refactoring and building/maintaining per-section models, more upfront work.

## Decision Outcome

We will implement model-driven, section-specific extraction and enrichment, with the following explicit actions:

- **Per-section extraction models:** For each core clinical section, build explicit extraction models (e.g., `ResultsPanel`, `ProblemObservation`, `MedicationAdministered`, `ImmunizationAdministration`) reflecting IG fields and table schema.
- **Terminology service update:** Do not store XPaths in terminology/config objects. Store codes separated by code system (SNOMED, RxNorm, LOINC, etc.), supporting per-section code system constraints based on IG/spec. When processing an entry with coded data, lookup in the appropriate code system for a match; if code system isn't present, entry is skipped unless IG/spec allows "any."
- **Dual section processing instructions:** Enable configuration of per-section instructions for both `<entry>` extraction and `<text>` narrative generation. Section processing for `<entry>` is modeled separately from `<text>`, allowing full IG-driven refinement. `<text>` generation and refining will initially only be implemented for four core sections: Results, Problems, Medications Administered, Immunizations; other sections will retain current behavior for narrative generation.
- **displayName enrichment:** Enrich displayName and other context during extraction, not post-processing.
- **Narrative generation:** For targeted sections, generate section narrative tables from extracted models, ensuring structure and content matches clinical entries.
- **Incremental rollout:** Roll out incrementally, starting with four core clinical sections, expanding as needed and as models/configs are prepared.
- **Future-proofed architecture:** Provides clean separation of terminology management, extraction logic, and narrative generation; enables easier jurisdictional customization and richer features going forward.

These actions ensure contextually accurate, IG-conformant, and maintainable enrichment and narrative generation. The model-driven approach delivers clinical integrity, technical clarity, and strong boundaries between configuration, extraction, and presentation—all supporting jurisdiction-based requirements and ongoing evolution.

### Approach Comparison Table

| Approach        | Clinical Integrity | Maintainability | IG Conformance | Performance | Future Proofing | RFC Alignment |
| --------------- | ------------------ | --------------- | -------------- | ----------- | --------------- | ------------- |
| Post-processing | ❌                 | 🤷              | ❌             | ✅          | ❌              | ❌            |
| Global Parsing  | 🤷                 | ❌              | ❌             | ❌          | ❌              | ❌            |
| Union XPath     | ❌                 | ❌              | ❌             | 🤷          | ❌              | ❌            |
| Model-driven    | ✅                 | ✅              | ✅             | ✅          | ✅              | ✅            |

## Implementation Evaluation & Best Practices

As outlined above, we recommend the following detailed implementation patterns to ensure our actions are robust and future-proof:

- **Per-section extraction models:** Expand `SectionSpecification`/`TriggerCode`/`EICRSpecification`, and build specific clinical models for each section (e.g., `ResultsPanel`, `ProblemObservation`), matching IG structure and schema.
- **Terminology decoupling:** Store codes by code system; do not embed XPaths/context in terminology/configuration. Reference “Code System Requirements By Section” from the implementation guide.
- **Dual section processing instructions:** Configure extraction and narrative instructions per section, keeping clear separation between entry refinement and text generation.
- **Enrichment during extraction:** Enrich displayNames and context as part of per-section extraction, using section code system and template constraints.
- **Narrative generation:** Build narrative tables/text from enriched models, with IG-driven structure and field mapping for clinical accuracy.
- **Incremental rollout:** Prioritize core sections; expand as new models come online.
- **Future-proofing:** Modularize terminology, extraction, and narrative logic for easy jurisdictional customization.

## Section Extraction & Narrative Specification for Initial Rollout

Below are the extraction and narrative requirements for the four target sections in the initial rollout. These specifications are driven by HL7 IG 3.1.1 and our internal CDA parsing guide.

### Results Section (LOINC: 30954-2)

- **Section XPath:**  
  `.//cda:section[cda:code/@code='30954-2']`
- **Entry Templates:**
  - Organizer: `templateId 2.16.840.1.113883.10.20.15.2.3.8`
  - Component Observation: `templateId 2.16.840.1.113883.10.20.15.2.3.5`
- **Fields to Extract:**
  - Panel Name (`Organizer/code/displayName`)
  - Observation Name (`Observation/code/displayName`)
  - Observation Code (`Observation/code/@code`)
  - Observation Value (`Observation/value/@value`)
  - Unit (`Observation/value/@unit`)
  - SNOMED/LOINC Mapping (TriggerCode, displayName)
  - Result Date (`Observation/effectiveTime/@value`)
- **Narrative Table Columns:**  
  | Panel | Name | Code | Value | Unit | Date | Code System |

### Problems Section (LOINC: 11450-4)

- **Section XPath:**  
  `.//cda:section[cda:code/@code='11450-4']`
- **Entry Template:**
  - Problem Observation: `templateId 2.16.840.1.113883.10.20.15.2.3.6`
- **Fields to Extract:**
  - Problem Name (`Observation/code/displayName`)
  - Problem Code (`Observation/code/@code`)
  - Status (`Observation/statusCode/@code`)
  - Onset Date (`Observation/effectiveTime/@value`)
  - SNOMED Mapping (TriggerCode, displayName)
- **Narrative Table Columns:**  
  | Name | Code | Status | Onset Date | Code System |

### Medications Administered Section (LOINC: 76409-9)

- **Section XPath:**  
  `.//cda:section[cda:code='76409-9']`
- **Entry Template:**
  - Medication Administered: `templateId 2.16.840.1.113883.10.20.15.2.3.1`
- **Fields to Extract:**
  - Medication Name (`SubstanceAdministration/consumable/manufacturedProduct/manufacturedMaterial/code/displayName`)
  - Medication Code (`.../code/@code`)
  - Route (`SubstanceAdministration/routeCode/@displayName`)
  - Dose (`SubstanceAdministration/doseQuantity/@value`)
  - Unit (`SubstanceAdministration/doseQuantity/@unit`)
  - Administration Date (`SubstanceAdministration/effectiveTime/@value`)
  - RxNorm Mapping (TriggerCode, displayName)
- **Narrative Table Columns:**  
  | Name | Code | Route | Dose | Unit | Date | Code System |

### Immunizations Section (LOINC: 59777-3)

- **Section XPath:**  
  `.//cda:section[cda:code='59777-3']`
- **Entry Template:**
  - Immunization Administered: `templateId 2.16.840.1.113883.10.20.15.2.3.3`
- **Fields to Extract:**
  - Immunization Name (`SubstanceAdministration/consumable/manufacturedProduct/manufacturedMaterial/code/displayName`)
  - Immunization Code (`.../code/@code`)
  - Dose (`SubstanceAdministration/doseQuantity/@value`)
  - Unit (`SubstanceAdministration/doseQuantity/@unit`)
  - Administration Date (`SubstanceAdministration/effectiveTime/@value`)
  - CVX/SNOMED Mapping (TriggerCode, displayName)
- **Narrative Table Columns:**  
  | Name | Code | Dose | Unit | Date | Code System |

## Code System Organization & Enrichment Approach

To maximize accuracy and maintainability, codes will be stored and matched by code system throughout all layers (database, configuration, enrichment, and clinical models).

- **ProcessedConfiguration Structure:**  
  Codes are organized within `CodeSystemSets` (SNOMED, LOINC, ICD-10, RxNorm, CVX, Custom, etc.), enabling efficient and unambiguous lookups during extraction and enrichment.
- **Matching Logic:**  
  The enrichment service and extraction models will use code system OIDs to select the appropriate set of codes within the configuration. This enables O(1) lookup and prevents mismatches or ambiguity across code systems.
- **DisplayName Enrichment:**  
  DisplayName enrichment occurs immediately after code matching. If displayName is missing from the XML, future enhancements may leverage a terminology database/service for enrichment.
- **Translation Elements:**  
  When CDA entries include translations (multiple code systems), extraction/enrichment will check both primary and translation codes for trigger and displayName matching.

_This structure aligns with HL7 IG and database storage patterns and supports incremental section rollout, robust matching, and clinical clarity in both extraction and narrative generation._

### Implementation Steps

**1. Refactor section models:** Expand SectionSpecification and related models to encapsulate extraction and narrative logic per section.  
**2. Update terminology config:** Split codes by code system, remove embedded XPaths; enable code system and template filtering at extraction.  
**3. Integrate displayName enrichment in extraction:** Perform enrichment at extraction time, matching code context in section and entry templates.  
**4. Enhance narrative generation:** Generate `<text>` tables/blocks using enriched section models, following IG layout.  
**5. Plan incremental rollout:** Prioritize Results, Problems, Medications, Immunizations; bring on other sections as models are built.  
**6. Document and expose model contracts:** Link extraction and narrative logic explicitly to IG and parsing guide patterns.

## Appendix

- [Initial displayName enrichment RFC](https://github.com/CDCgov/dibbs-ecr-refiner/blob/main/docs/decisions/0005_2026-02-18_display-name-enrichment.md)
