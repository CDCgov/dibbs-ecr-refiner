# 6. displayName Enrichment and Better Search

Date: 2026-03-07

## Status

Accepted

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

Below are the corrected extraction and narrative requirements for the four target sections in the initial rollout. These specifications are driven by HL7 C-CDA R2.1 and eICR IG STU 1.1 / STU 3.1.1 constraints, cross-referenced against the source Implementation Guides.

> [!IMPORTANT]
> **This section replaces the original "Section Extraction & Narrative Specification for Initial Rollout" in RFC 0006.** The original contained incorrect LOINC codes, fabricated templateIds, and wrong extraction paths. All values below have been verified against CDAR2_IG_PHCASERPT_R2_STU1_1_2017JAN Vol2 and CDAR2_IG_PHCASERPT_R2_STU3_1_1_Vol2_2022JUL_2024OCT.

### Confidence Tiers

Each section and its code match points are annotated with a confidence tier:

- **Tier 1 (Rigid):** The IG uses SHALL on both the structural path and the code system. Hard-code these paths.
- **Tier 2 (Expected with fallback):** The IG uses SHOULD on the code system or the value type is open-ended. Search by expected code system first, fall back to translations or other systems.

---

### Results Section (LOINC: `30954-2`) — Tier 2

- **Section XPath:**
  `.//cda:section[cda:code/@code='30954-2']`
- **Section templateId:** `2.16.840.1.113883.10.20.22.2.3.1` ext `2015-08-01`
  - Source: [STU1.1-V2] CONF:1198-9137

- **Entry Structure:**

  ```
  entry [1..*] (SHALL, CONF:1198-7112)
   └─ organizer  [Result Organizer (V3)]
       ├─ code          ← PANEL CODE (Tier 2: SHOULD be LOINC or SNOMED, MAY be CPT-4)
       └─ component [1..*] (SHALL, CONF:1198-7124)
           └─ observation  [Result Observation (V3)]
               ├─ code   ← TEST CODE (Tier 2: SHOULD be LOINC)
               └─ value  ← RESULT VALUE (Tier 2: type varies; if CD, SHOULD be SNOMED)
  ```

- **Entry Templates:**

  | Template                | templateId `@root`               | `@extension` | Source         |
  | ----------------------- | -------------------------------- | ------------ | -------------- |
  | Result Organizer (V3)   | `2.16.840.1.113883.10.20.22.4.1` | `2015-08-01` | CONF:1198-9134 |
  | Result Observation (V3) | `2.16.840.1.113883.10.20.22.4.2` | `2015-08-01` | CONF:1198-9138 |

- **Code Match Points:**

  | Match Point                  | Relative XPath from `<entry>`                                                                          | Expected Code System     | Code System OID                    | Tier | Source                          |
  | ---------------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------ | ---------------------------------- | ---- | ------------------------------- |
  | Test Code (observation code) | `.//hl7:observation[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.2']]/hl7:code`                  | LOINC (SHOULD)           | `2.16.840.1.113883.6.1`            | 2    | CONF:1198-7133, CONF:1198-19212 |
  | Result Value (if coded)      | `.//hl7:observation[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.2']]/hl7:value[@xsi:type='CD']` | SNOMED (SHOULD)          | `2.16.840.1.113883.6.96`           | 2    | CONF:1198-32610                 |
  | Panel Code (organizer)       | `.//hl7:organizer/hl7:code`                                                                            | LOINC or SNOMED (SHOULD) | `2.16.840.1.113883.6.1` or `.6.96` | 2    | CONF:1198-19218                 |

- **Pruning Granularity:** Component-level. Within a Result Organizer, remove individual `<component>` elements whose Result Observations don't match, rather than removing the whole entry. Keep the organizer if at least one component matches.

- **Fields to Extract:**

  | Field            | XPath (relative to observation)                          | Source          |
  | ---------------- | -------------------------------------------------------- | --------------- |
  | Panel Name       | `ancestor::hl7:organizer/hl7:code/@displayName`          | Organizer code  |
  | Test Name        | `hl7:code/@displayName`                                  | CONF:1198-7133  |
  | Test Code        | `hl7:code/@code`                                         | CONF:1198-7133  |
  | Test Code System | `hl7:code/@codeSystem`                                   | CONF:1198-7133  |
  | Result Value     | `hl7:value/@value` (PQ) or `hl7:value/@displayName` (CD) | CONF:1198-7143  |
  | Unit             | `hl7:value/@unit` (PQ only)                              | CONF:1198-31484 |
  | Result Date      | `hl7:effectiveTime/@value`                               | CONF:1198-7140  |

- **Narrative Table Columns:**
  | Panel | Test Name | Code | Value | Unit | Date | Code System |

> [!NOTE]
> The Result Observation `code` SHOULD be LOINC, but the IG explicitly allows local codes: "If an appropriate LOINC code does not exist, then the local code for this result SHALL be sent" (CONF:1198-19212). The `value` element type is not constrained — it could be PQ (physical quantity), CD (coded), ST (string), or other types. Only coded values (CD) have a matchable code; for PQ/ST results, match on the observation `code` instead.

> [!TIP]
> **Trigger codes on Result Observations** can appear on EITHER `code` (test name) OR `value` (organism/substance) OR BOTH. The `@sdtc:valueSet="2.16.840.1.114222.4.11.7508"` marker tells you which element(s) carry trigger codes. Source: CONF:3284-300.

---

### Problems Section (LOINC: `11450-4`) — Tier 1

- **Section XPath:**
  `.//cda:section[cda:code/@code='11450-4']`
- **Section templateId:** `2.16.840.1.113883.10.20.22.2.5.1` ext `2015-08-01`
  - Source: [STU1.1-V2] CONF:1198-10441

- **Entry Structure:**

  ```
  entry [1..*] (SHALL, CONF:1198-9183)
   └─ act  [Problem Concern Act (V3)]
       └─ entryRelationship [@typeCode="SUBJ"] [1..*] (SHALL, CONF:1198-9034)
           └─ observation  [Problem Observation (V3)]
               ├─ code    ← PROBLEM TYPE (e.g. "Condition", "Complaint") — NOT the diagnosis
               └─ value   ← CONDITION CODE ← YOUR MATCH POINT (Tier 1: SHALL be SNOMED)
  ```

- **Entry Templates:**

  | Template                 | templateId `@root`               | `@extension` | Source          |
  | ------------------------ | -------------------------------- | ------------ | --------------- |
  | Problem Concern Act (V3) | `2.16.840.1.113883.10.20.22.4.3` | `2015-08-01` | CONF:1198-16773 |
  | Problem Observation (V3) | `2.16.840.1.113883.10.20.22.4.4` | `2015-08-01` | CONF:1198-14927 |

- **Code Match Points:**

  | Match Point                    | Relative XPath from `<entry>`                                                                          | Expected Code System | Code System OID          | Tier | Source                   |
  | ------------------------------ | ------------------------------------------------------------------------------------------------------ | -------------------- | ------------------------ | ---- | ------------------------ |
  | Condition Code (primary)       | `.//hl7:observation[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]/hl7:value`                 | SNOMED CT (SHALL)    | `2.16.840.1.113883.6.96` | 1    | CONF:1198-9058, Table 94 |
  | ICD-10 Translation (secondary) | `.//hl7:observation[hl7:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]/hl7:value/hl7:translation` | ICD-10-CM (MAY)      | `2.16.840.1.113883.6.90` | 1    | CONF:1198-16750          |

- **Pruning Granularity:** Entry-level. The Problem Concern Act is a wrapper; if any child Problem Observation matches, keep the entire entry. If none match, remove the entry.

- **Fields to Extract:**

  | Field                 | XPath (relative to Problem Observation)                                 | Source          |
  | --------------------- | ----------------------------------------------------------------------- | --------------- |
  | Condition Name        | `hl7:value/@displayName`                                                | CONF:1198-9058  |
  | Condition Code        | `hl7:value/@code`                                                       | CONF:1198-9058  |
  | Condition Code System | `hl7:value/@codeSystem`                                                 | CONF:1198-9058  |
  | ICD-10 Translation    | `hl7:value/hl7:translation[@codeSystem='2.16.840.1.113883.6.90']/@code` | CONF:1198-16750 |
  | Problem Type          | `hl7:code/@displayName`                                                 | CONF:1198-9045  |
  | Status                | `hl7:statusCode/@code` (always "completed")                             | CONF:1198-19112 |
  | Onset Date            | `hl7:effectiveTime/hl7:low/@value`                                      | CONF:1198-15603 |
  | Resolution Date       | `hl7:effectiveTime/hl7:high/@value`                                     | CONF:1198-15604 |

- **Narrative Table Columns:**
  | Condition Name | Code | Code System | Status | Onset Date | Resolution Date |

> [!IMPORTANT]
> **Do NOT match on `observation/code`.** The `code` element on Problem Observation represents the Problem Type (e.g., SNOMED `64572001` "Condition" or LOINC `75323-6` "Condition") — it is NOT the patient's diagnosis. The actual condition/diagnosis code is in `observation/value`. Source: CONF:1198-9045 (code = Problem Type value set) vs CONF:1198-9058 (value = Problem value set, which is SNOMED clinical findings).

> [!TIP]
> **ICD-10 translations:** Many EHRs send an ICD-10-CM translation alongside the primary SNOMED code in `value/translation`. Check `value/@code` (SNOMED) first as the primary match, then `value/translation/@code` where `@codeSystem='2.16.840.1.113883.6.90'` as a secondary match. This gives two chances to match a condition against the configuration.

> [!NOTE]
> **negationInd:** Problem Observation MAY carry `@negationInd` (CONF:1198-10139). When `true`, it negates the value — e.g., `negationInd="true"` with `value/@code="64572001"` means "no known disease." Skip observations with `negationInd="true"`.

---

### Medications Administered Section (LOINC: `29549-3`) — Tier 1

- **Section XPath:**
  `.//cda:section[cda:code/@code='29549-3']`
- **Section templateId:** `2.16.840.1.113883.10.20.22.2.38` ext `2014-06-09`
  - Source: [STU1.1-V2] CONF:1098-10405

- **Entry Structure:**

  ```
  entry [0..*] (MAY, CONF:1098-8156)
   └─ substanceAdministration  [Medication Activity (V2)]
       └─ consumable (SHALL, CONF:1098-7520)
           └─ manufacturedProduct  [Medication Information (V2)] (SHALL, CONF:1098-16085)
               └─ manufacturedMaterial (SHALL, CONF:1098-7411)
                   └─ code  ← DRUG CODE ← YOUR MATCH POINT (Tier 1: SHALL be RxNorm)
  ```

- **Entry Templates:**

  | Template                    | templateId `@root`                | `@extension` | Source          |
  | --------------------------- | --------------------------------- | ------------ | --------------- |
  | Medication Activity (V2)    | `2.16.840.1.113883.10.20.22.4.16` | `2014-06-09` | CONF:1098-10504 |
  | Medication Information (V2) | `2.16.840.1.113883.10.20.22.4.23` | `2014-06-09` | CONF:1098-10506 |

- **Code Match Points:**

  | Match Point                                | Relative XPath from `<entry>`                          | Expected Code System          | Code System OID          | Tier | Source                   |
  | ------------------------------------------ | ------------------------------------------------------ | ----------------------------- | ------------------------ | ---- | ------------------------ |
  | Drug Code (primary)                        | `.//hl7:manufacturedMaterial/hl7:code`                 | RxNorm (SHALL)                | `2.16.840.1.113883.6.88` | 1    | CONF:1098-7412, Table 79 |
  | Clinical Substance Translation (secondary) | `.//hl7:manufacturedMaterial/hl7:code/hl7:translation` | RxNorm, UNII, or SNOMED (MAY) | multiple                 | 2    | CONF:1098-31884          |

- **Pruning Granularity:** Entry-level. Each entry contains one Medication Activity; keep or remove the whole entry.

- **Fields to Extract:**

  | Field                  | XPath (relative to substanceAdministration)                                             | Source         |
  | ---------------------- | --------------------------------------------------------------------------------------- | -------------- |
  | Medication Name        | `hl7:consumable/hl7:manufacturedProduct/hl7:manufacturedMaterial/hl7:code/@displayName` | CONF:1098-7412 |
  | Medication Code        | `hl7:consumable/hl7:manufacturedProduct/hl7:manufacturedMaterial/hl7:code/@code`        | CONF:1098-7412 |
  | Medication Code System | `hl7:consumable/hl7:manufacturedProduct/hl7:manufacturedMaterial/hl7:code/@codeSystem`  | CONF:1098-7412 |
  | Route                  | `hl7:routeCode/@displayName`                                                            | CONF:1098-7514 |
  | Dose                   | `hl7:doseQuantity/@value`                                                               | CONF:1098-7516 |
  | Dose Unit              | `hl7:doseQuantity/@unit`                                                                | CONF:1098-7526 |
  | Administration Date    | `hl7:effectiveTime/@value` or `hl7:effectiveTime/hl7:low/@value`                        | CONF:1098-7508 |

- **Narrative Table Columns:**
  | Medication Name | Code | Route | Dose | Unit | Date | Code System |

> [!NOTE]
> **Do NOT match on `substanceAdministration/code`.** That element is MAY (CONF:1098-7506) and represents the type of administration, not the drug. The drug code is always inside `consumable/manufacturedProduct/manufacturedMaterial/code`. Source: [STU1.1-V2] Table 76.

---

### Immunizations Section (LOINC: `11369-6`) — Tier 1

- **Section XPath:**
  `.//cda:section[cda:code/@code='11369-6']`
- **Section templateId:** `2.16.840.1.113883.10.20.22.2.2.1` ext `2015-08-01`
  - Source: [STU1.1-V2] CONF:1198-10400 (entries required variant)

- **Entry Structure:**

  ```
  entry [0..*] (SHOULD, CONF:1198-7969)
   └─ substanceAdministration  [Immunization Activity (V3)]
       └─ consumable (SHALL, CONF:1198-8847)
           └─ manufacturedProduct  [Immunization Medication Information (V2)] (SHALL, CONF:1198-15546)
               └─ manufacturedMaterial (SHALL, CONF:1098-9006)
                   └─ code  ← VACCINE CODE ← YOUR MATCH POINT (Tier 1: SHALL be CVX)
  ```

- **Entry Templates:**

  | Template                                 | templateId `@root`                | `@extension` | Source          |
  | ---------------------------------------- | --------------------------------- | ------------ | --------------- |
  | Immunization Activity (V3)               | `2.16.840.1.113883.10.20.22.4.52` | `2015-08-01` | CONF:1198-10498 |
  | Immunization Medication Information (V2) | `2.16.840.1.113883.10.20.22.4.54` | `2014-06-09` | CONF:1098-10499 |

- **Code Match Points:**

  | Match Point                    | Relative XPath from `<entry>`                          | Expected Code System | Code System OID            | Tier | Source                   |
  | ------------------------------ | ------------------------------------------------------ | -------------------- | -------------------------- | ---- | ------------------------ |
  | Vaccine Code (primary)         | `.//hl7:manufacturedMaterial/hl7:code`                 | CVX (SHALL)          | `2.16.840.1.113883.12.292` | 1    | CONF:1098-9007, Table 72 |
  | RxNorm Translation (secondary) | `.//hl7:manufacturedMaterial/hl7:code/hl7:translation` | RxNorm (MAY)         | `2.16.840.1.113883.6.88`   | 2    | CONF:1098-31543          |

- **Pruning Granularity:** Entry-level. Each entry contains one Immunization Activity; keep or remove the whole entry.

- **Fields to Extract:**

  | Field               | XPath (relative to substanceAdministration)                                             | Source         |
  | ------------------- | --------------------------------------------------------------------------------------- | -------------- |
  | Vaccine Name        | `hl7:consumable/hl7:manufacturedProduct/hl7:manufacturedMaterial/hl7:code/@displayName` | CONF:1098-9007 |
  | Vaccine Code        | `hl7:consumable/hl7:manufacturedProduct/hl7:manufacturedMaterial/hl7:code/@code`        | CONF:1098-9007 |
  | Vaccine Code System | `hl7:consumable/hl7:manufacturedProduct/hl7:manufacturedMaterial/hl7:code/@codeSystem`  | CONF:1098-9007 |
  | Dose                | `hl7:doseQuantity/@value`                                                               | CONF:1198-8841 |
  | Dose Unit           | `hl7:doseQuantity/@unit`                                                                | CONF:1198-8842 |
  | Administration Date | `hl7:effectiveTime/@value`                                                              | CONF:1198-8834 |
  | Lot Number          | `hl7:consumable/hl7:manufacturedProduct/hl7:manufacturedMaterial/hl7:lotNumberText`     | CONF:1098-9014 |

- **Narrative Table Columns:**
  | Vaccine Name | Code | Dose | Unit | Date | Code System |

> [!TIP]
> **RxNorm translations on immunizations:** The vaccine `code` element MAY contain `translation` elements from the Vaccine Clinical Drug value set, which uses RxNorm (`2.16.840.1.113883.6.88`) per CONF:1098-31543. If your condition configurations include RxNorm codes for vaccines, check `code/translation/@code` as a secondary match after the primary CVX match.

> [!NOTE]
> **negationInd on Immunization Activity:** `@negationInd` is SHALL (CONF:1198-8985). When `true`, it means the immunization was NOT given. Your matcher should skip entries with `negationInd="true"` since they represent refusals, not administrations.

---

### Summary of Corrections from Original RFC

| Item                              | Original (Incorrect)                                          | Corrected                                                              | Source          |
| --------------------------------- | ------------------------------------------------------------- | ---------------------------------------------------------------------- | --------------- |
| Medications Administered LOINC    | `76409-9`                                                     | **`29549-3`**                                                          | CONF:1098-15384 |
| Immunizations LOINC               | `59777-3`                                                     | **`11369-6`**                                                          | CONF:1198-15368 |
| Medications Administered XPath    | `.//cda:section[cda:code='76409-9']`                          | **`.//cda:section[cda:code/@code='29549-3']`**                         | —               |
| Immunizations XPath               | `.//cda:section[cda:code='59777-3']`                          | **`.//cda:section[cda:code/@code='11369-6']`**                         | —               |
| Results Organizer templateId      | `2.16.840.1.113883.10.20.15.2.3.8` (nonexistent)              | **`2.16.840.1.113883.10.20.22.4.1`** (C-CDA Result Organizer V3)       | CONF:1198-9134  |
| Results Observation templateId    | `2.16.840.1.113883.10.20.15.2.3.5` (Initiation Reason Obs)    | **`2.16.840.1.113883.10.20.22.4.2`** (C-CDA Result Observation V3)     | CONF:1198-9138  |
| Problem Observation templateId    | `2.16.840.1.113883.10.20.15.2.3.6` (nonexistent)              | **`2.16.840.1.113883.10.20.22.4.4`** (C-CDA Problem Observation V3)    | CONF:1198-14927 |
| Medications entry templateId      | `2.16.840.1.113883.10.20.15.2.3.1` (Travel History)           | **`2.16.840.1.113883.10.20.22.4.16`** (C-CDA Medication Activity V2)   | CONF:1098-10504 |
| Immunizations entry templateId    | `2.16.840.1.113883.10.20.15.2.3.3` (Trigger Code Problem Obs) | **`2.16.840.1.113883.10.20.22.4.52`** (C-CDA Immunization Activity V3) | CONF:1198-10498 |
| Problem condition code extraction | `Observation/code/displayName`                                | **`Observation/value/@displayName`** and **`Observation/value/@code`** | CONF:1198-9058  |

---

### Code System Constraints by Section

This table summarizes the mandated code systems per section, supporting per-section code system filtering during extraction and matching. This replaces the generic "Code System Organization" section in the original RFC.

| Section                | Match Element               | Primary Code System | Primary OID                | Tier       | Secondary (translation) | Secondary OID            |
| ---------------------- | --------------------------- | ------------------- | -------------------------- | ---------- | ----------------------- | ------------------------ |
| Problems               | `observation/value`         | SNOMED CT           | `2.16.840.1.113883.6.96`   | 1 (SHALL)  | ICD-10-CM               | `2.16.840.1.113883.6.90` |
| Results (test code)    | `observation/code`          | LOINC               | `2.16.840.1.113883.6.1`    | 2 (SHOULD) | local codes             | varies                   |
| Results (result value) | `observation/value` (if CD) | SNOMED CT           | `2.16.840.1.113883.6.96`   | 2 (SHOULD) | —                       | —                        |
| Medications            | `manufacturedMaterial/code` | RxNorm              | `2.16.840.1.113883.6.88`   | 1 (SHALL)  | SNOMED/UNII             | varies                   |
| Immunizations          | `manufacturedMaterial/code` | CVX                 | `2.16.840.1.113883.12.292` | 1 (SHALL)  | RxNorm                  | `2.16.840.1.113883.6.88` |

---

_Sources: CDAR2_IG_PHCASERPT_R2_STU1_1_2017JAN Vol2, CDAR2_IG_PHCASERPT_R2_STU3_1_1_Vol2_2022JUL_2024OCT, and Keith Boone's "The CDA Book." CONF numbers reference the STU 1.1 constraint table identifiers unless otherwise noted._## Appendix

- [Initial displayName enrichment RFC](https://github.com/CDCgov/dibbs-ecr-refiner/blob/main/docs/decisions/0005_2026-02-18_display-name-enrichment.md)
