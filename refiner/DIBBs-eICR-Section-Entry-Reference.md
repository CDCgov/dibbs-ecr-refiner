# eICR/RR Section & Entry Code-Matching Reference

## Purpose

This document serves as a code-matching reference for a Python application that filters eICR entries by reportable condition. It categorizes every relevant section, entry template, and coded element into three tiers based on **how rigid the IG constraints are** — so the parser can be inflexible when appropriate and flexible when necessary.

**Certainty tiers:**

- **Tier 1 — Rigid**: The IG uses SHALL on both the structural path and the code system. Hard-code these paths. If the data isn't where the spec says it must be, it's non-conformant and you can reject it.
- **Tier 2 — Expected with fallback**: The IG uses SHOULD on the code system or the element's type is open-ended. Search by the expected code system first, then fall back to inspecting translations or accepting other systems.
- **Tier 3 — No enforced structure**: Narrative-only sections or sections with no mandatory coded entries your pipeline can match against. Skip or handle holistically.

**Source materials cited:**

- `[STU1.1-V2]` = CDAR2_IG_PHCASERPT_R2_STU1_1_2017JAN Vol2
- `[STU3.1.1-V2]` = CDAR2_IG_PHCASERPT_R2_STU3_1_1_Vol2_2022JUL_2024OCT
- `[RR-V2]` = CDAR2_IG_PHCR_R2_RR_STU1_1_Vol2
- `[CDA Book]` = Keith Boone, "The CDA Book"
- `[General CDA]` = General CDA/C-CDA implementation knowledge (not directly sourced from project IGs — treat with appropriate caution)

---

## Part 1: RR Parsing — Extracting Reportable Conditions and Jurisdictions

Before touching the eICR, the application reads the RR to determine which SNOMED condition codes are reportable and for which jurisdictions. This is entirely Tier 1 — every element in this chain uses SHALL.

### Traversal Path

```
RR ClinicalDocument
 └─ component/structuredBody
     └─ component/section  [Reportability Response Information Section]
         └─ entry
             └─ organizer  [Reportability Response Coded Information Organizer]
                 └─ component (1..*)
                     └─ observation  [Relevant Reportable Condition Observation]
                         ├─ value [@xsi:type="CD"]  ← SNOMED condition code
                         └─ entryRelationship (1..*)
                             └─ organizer  [Reportability Information Organizer]
                                 ├─ code  ← Location Relevance
                                 ├─ participant  [Responsible Agency]
                                 ├─ participant  [Routing Entity]
                                 └─ component
                                     └─ observation  [Determination of Reportability]
                                         └─ value [@code="RRVS1"]  ← filter here
```

### Key Templates and OIDs

| Template                                           | templateId @root                    | @extension   | Source                                                     |
| -------------------------------------------------- | ----------------------------------- | ------------ | ---------------------------------------------------------- |
| Reportability Response Coded Information Organizer | `2.16.840.1.113883.10.20.15.2.3.34` | `2017-04-01` | [RR-V2] Table 259 / [STU3.1.1-V2] Table 259, CONF:3315-137 |
| Relevant Reportable Condition Observation          | `2.16.840.1.113883.10.20.15.2.3.12` | `2017-04-01` | [RR-V2] Table 69, CONF:3315-225                            |
| Reportability Information Organizer                | `2.16.840.1.113883.10.20.15.2.3.13` | `2017-04-01` | [RR-V2] Table 71, CONF:3315-239                            |
| Determination of Reportability                     | `2.16.840.1.113883.10.20.15.2.3.19` | `2017-04-01` | [RR-V2] Table 32, CONF:3315-349                            |

### Code Extraction Points (all Tier 1 / SHALL)

**Condition SNOMED code:**

- Element: `Relevant Reportable Condition Observation / value`
- Type: `@xsi:type="CD"` (CONF:3315-552)
- Code system: SHALL be SNOMED CT `2.16.840.1.113883.6.96` (CONF:3315-552)
- The `code` element on this observation is always fixed: `@code="64572001"` (Condition) from SNOMED (CONF:3315-554/555)
- Source: [RR-V2] Table 69

**Determination of Reportability:**

- Element: `Determination of Reportability / value`
- Type: `@xsi:type="CD"` (CONF:3315-353)
- Value set: Determination of Reportability (eCR) `2.16.840.1.113883.10.20.15.2.5.3`
- Code system: PHIN VS (CDC Local Coding System) `2.16.840.1.114222.4.5.274`
- Filter for: `@code="RRVS1"` (Reportable)
- Other codes: RRVS2 (May be reportable), RRVS3 (Not reportable), RRVS4 (No rule met)
- Source: [RR-V2] Table 33

**Jurisdiction identification:**

- The Reportability Information Organizer contains participant elements for the Responsible Agency (templateId `15.2.4.2`, SHOULD, CONF:3315-338) and Routing Entity (templateId `15.2.4.1`, SHALL, CONF:3315-543). Use these to identify the jurisdiction.
- The organizer's `code` element indicates Location Relevance (patient home vs provider facility) from value set `2.16.840.1.113883.10.20.15.2.5.6` (CONF:3315-581).
- Source: [RR-V2] Table 71

### Algorithm

```
for each Relevant Reportable Condition Observation:
    snomed_code = observation/value/@code
    for each child Reportability Information Organizer:
        determination = organizer/component/observation[Determination of Reportability]/value/@code
        if determination == "RRVS1":
            jurisdiction = extract from Responsible Agency or Routing Entity participant
            add (snomed_code, jurisdiction) to reportable set
deduplicate by snomed_code, keeping jurisdiction list as values
```

---

## Part 2: Section Identification (all Tier 1)

Every section SHALL have a `code` element with a fixed LOINC code. This is the most reliable way to identify sections.

| Section                    | LOINC `code/@code` | `code/@codeSystem`      | templateId `@root`                  | Conformance in STU 1.1 | Source                      |
| -------------------------- | ------------------ | ----------------------- | ----------------------------------- | ---------------------- | --------------------------- |
| Encounters                 | `46240-8`          | `2.16.840.1.113883.6.1` | `2.16.840.1.113883.10.20.22.2.22.1` | SHALL                  | [STU1.1-V2] CONF:1198-15467 |
| Problem                    | `11450-4`          | `2.16.840.1.113883.6.1` | `2.16.840.1.113883.10.20.22.2.5.1`  | SHALL                  | [STU1.1-V2] CONF:1198-15410 |
| Results                    | `30954-2`          | `2.16.840.1.113883.6.1` | `2.16.840.1.113883.10.20.22.2.3.1`  | SHALL                  | [STU1.1-V2] CONF:1198-15434 |
| Medications Administered   | `29549-3`          | `2.16.840.1.113883.6.1` | `2.16.840.1.113883.10.20.22.2.38`   | SHALL                  | [STU1.1-V2] CONF:1098-15384 |
| Immunizations              | `11369-6`          | `2.16.840.1.113883.6.1` | `2.16.840.1.113883.10.20.22.2.2.1`  | SHOULD                 | [STU1.1-V2] CONF:1198-15368 |
| Social History             | `29762-2`          | `2.16.840.1.113883.6.1` | `2.16.840.1.113883.10.20.22.2.17`   | SHALL                  | [STU1.1-V2] CONF:1198-14820 |
| Plan of Treatment          | `18776-5`          | `2.16.840.1.113883.6.1` | `2.16.840.1.113883.10.20.22.2.10`   | MAY                    | [STU1.1-V2] CONF:1098-14750 |
| History of Present Illness | `10164-2`          | `2.16.840.1.113883.6.1` | `1.3.6.1.4.1.19376.1.5.3.1.3.4`     | SHALL                  | [STU1.1-V2] CONF:81-15478   |
| Reason for Visit           | `29299-5`          | `2.16.840.1.113883.6.1` | `2.16.840.1.113883.10.20.22.2.12`   | SHALL                  | [STU1.1-V2] CONF:81-15430   |

> [!TIP]
> Match sections by `section/code/@code` (the LOINC code) rather than solely by templateId. The LOINC code is a single fixed value with no extension versioning to worry about, and some senders may omit or vary the templateId extension. Both approaches work on conformant documents, but LOINC is more tolerant of minor sender deviations.

> [!NOTE]
> In STU 3.1.1, many additional sections appear (Chief Complaint `10154-3`, Assessment and Plan `51847-2`, Vital Signs `8716-3`, Pregnancy, Procedures, etc.). For version-independent parsing, if your code encounters a section LOINC it doesn't recognize, skip it gracefully.

---

## Part 3: Tier 1 Sections — Rigid Entry Parsing

These sections have mandatory entry templates with SHALL constraints on both the structural path to the coded element and the code system. Hard-code the XPaths and expected code systems.

### 3.1 Problem Section (LOINC `11450-4`)

**Entry structure (SHALL):**

```
section
 └─ entry [1..*]
     └─ act  [Problem Concern Act]
         └─ entryRelationship [@typeCode="SUBJ"]
             └─ observation  [Problem Observation]
                 └─ value [@xsi:type="CD"]  ← YOUR MATCH POINT
```

**Code match point:** `observation/value`

| Attribute           | Constraint         | Value                                                  | Source                                          |
| ------------------- | ------------------ | ------------------------------------------------------ | ----------------------------------------------- |
| `value/@xsi:type`   | SHALL              | `CD`                                                   | [STU1.1-V2] CONF:1198-9058                      |
| `value/@code`       | SHALL be from      | Problem value set `2.16.840.1.113883.3.88.12.3221.7.4` | [STU1.1-V2] Table 94                            |
| `value/@codeSystem` | Effectively always | SNOMED CT `2.16.840.1.113883.6.96`                     | [STU1.1-V2] Table 94 (value set is SNOMED-only) |

The Problem value set is defined as SNOMED CT codes descending from Clinical Findings (`404684003`) or Situation with Explicit Context (`243796009`). Source: [STU1.1-V2] Table 94.

> [!TIP]
> **ICD-10 translations**: The Problem Observation `value` element MAY contain `translation` elements where `translation/@code` MAY be from ICD-10-CM (`2.16.840.1.113883.6.90`) per CONF:1198-16750. Many EHRs send an ICD-10 translation alongside the SNOMED primary code. **For your matching logic**: check `value/@code` (SNOMED) first as your primary match, then check `value/translation/@code` for ICD-10-CM as a secondary match. This gives you two chances to match a condition code against your configuration. Source: [STU1.1-V2] Table 93.

**Nesting note:** Problem Concern Act is a wrapper (`act/code/@code="CONC"`). It SHALL contain at least one Problem Observation via `entryRelationship[@typeCode="SUBJ"]` (CONF:1198-9034). When deciding whether to keep or remove an entry, operate at the Problem Concern Act level — if any child Problem Observation matches, keep the whole act. If none match, remove the entire `<entry>` containing the act.

> [!NOTE]
> **negationInd**: Problem Observation MAY carry `@negationInd` (CONF:1198-10139). When `negationInd="true"`, it negates the value — e.g., `negationInd="true"` with `value/@code="64572001"` (Disease) means "no known disease." Your matcher should skip observations with `negationInd="true"` since they explicitly assert the absence of the condition. Source: [STU1.1-V2] CONF:1198-10139 and note at line 5482.

**Encounter Diagnosis also uses Problem Observation:** The Encounters section's Encounter Activity MAY contain Encounter Diagnosis (templateId `2.16.840.1.113883.10.20.22.4.80`), which itself SHALL contain Problem Observation(s) with the same `value` structure. The same matching logic applies. Source: [STU1.1-V2] Table 59, CONF:1198-14898.

---

### 3.2 Immunizations Section (LOINC `11369-6`)

**Entry structure (SHOULD in entries-optional, SHALL in entries-required):**

```
section
 └─ entry [0..*]
     └─ substanceAdministration  [Immunization Activity]
         └─ consumable
             └─ manufacturedProduct  [Immunization Medication Information]
                 └─ manufacturedMaterial
                     └─ code  ← YOUR MATCH POINT
```

**Code match point:** `substanceAdministration/consumable/manufacturedProduct/manufacturedMaterial/code`

| Attribute          | Constraint         | Value                                                    | Source                     |
| ------------------ | ------------------ | -------------------------------------------------------- | -------------------------- |
| `code/@code`       | SHALL be from      | CVX Vaccines Administered `2.16.840.1.113762.1.4.1010.6` | [STU1.1-V2] CONF:1098-9007 |
| `code/@codeSystem` | Effectively always | CVX `2.16.840.1.113883.12.292`                           | [STU1.1-V2] Table 72       |

> [!TIP]
> **RxNorm translations on immunizations**: The `code` element MAY contain `translation` elements from the Vaccine Clinical Drug value set (`2.16.840.1.113762.1.4.1010.8`), which uses RxNorm (`2.16.840.1.113883.6.88`) per CONF:1098-31543. If your condition configurations include RxNorm codes for vaccines, check `code/translation/@code` as a secondary match after the primary CVX match. Source: [STU1.1-V2] Table 71.

---

### 3.3 Medications Administered Section (LOINC `29549-3`)

**Entry structure (MAY — entries are optional in this section):**

```
section
 └─ entry [0..*]
     └─ substanceAdministration  [Medication Activity]
         └─ consumable
             └─ manufacturedProduct  [Medication Information]
                 └─ manufacturedMaterial
                     └─ code  ← YOUR MATCH POINT
```

**Code match point:** `substanceAdministration/consumable/manufacturedProduct/manufacturedMaterial/code`

| Attribute          | Constraint         | Value                                                   | Source                     |
| ------------------ | ------------------ | ------------------------------------------------------- | -------------------------- |
| `code/@code`       | SHALL be from      | Medication Clinical Drug `2.16.840.1.113762.1.4.1010.4` | [STU1.1-V2] CONF:1098-7412 |
| `code/@codeSystem` | Effectively always | RxNorm `2.16.840.1.113883.6.88`                         | [STU1.1-V2] Table 79       |

> [!NOTE]
> **Do not match on `substanceAdministration/code`** — that element is MAY (CONF:1098-7506) and is about the type of administration, not the drug. The drug code is always deeper, inside `consumable/manufacturedProduct/manufacturedMaterial/code`. Source: [STU1.1-V2] Table 76.

> [!TIP]
> **Clinical Substance translations**: The medication `code` MAY contain `translation` elements from the Clinical Substance value set (`2.16.840.1.113762.1.4.1010.2`), which is a grouping of RxNorm, UNII, and SNOMED CT substance codes (CONF:1098-31884). If you need to match SNOMED substance codes, check these translations. Source: [STU1.1-V2] Table 80.

---

## Part 4: Tier 2 Sections — Expected Structure with Fallback

These sections have mandatory entries but the coded element's code system is SHOULD rather than SHALL, or the value type is open-ended. Search by expected system first, then fall back.

### 4.1 Results Section (LOINC `30954-2`)

**Entry structure (SHALL):**

```
section
 └─ entry [1..*]
     └─ organizer  [Result Organizer]
         ├─ code  ← ORGANIZER-LEVEL MATCH POINT (Tier 2)
         └─ component [1..*]
             └─ observation  [Result Observation]
                 ├─ code  ← OBSERVATION TEST CODE (Tier 2)
                 └─ value  ← OBSERVATION RESULT VALUE (Tier 2, type varies)
```

There are THREE potential match points in this section, and all are Tier 2.

**4.1.1 Result Organizer `code` (Tier 2)**

| Attribute    | Constraint       | Value                            | Source                      |
| ------------ | ---------------- | -------------------------------- | --------------------------- |
| `code`       | SHALL be present | (CONF:1198-7128)                 | [STU1.1-V2] Table 110       |
| `code/@code` | SHOULD be from   | LOINC or SNOMED CT; MAY be CPT-4 | [STU1.1-V2] CONF:1198-19218 |

The organizer code typically represents a panel (e.g., LOINC `57021-8` "CBC W Auto Differential panel"). It's often LOINC but the spec only says SHOULD. Search LOINC first; if not LOINC, check SNOMED; if neither, log and skip. Source: [STU1.1-V2] CONF:1198-19218/19219.

**4.1.2 Result Observation `code` (Tier 2)**

| Attribute    | Constraint       | Value                         | Source                     |
| ------------ | ---------------- | ----------------------------- | -------------------------- |
| `code`       | SHALL be present | (CONF:1198-7133)              | [STU1.1-V2] Table 101      |
| `code/@code` | SHOULD be from   | LOINC `2.16.840.1.113883.6.1` | [STU1.1-V2] CONF:1198-7133 |

The spec explicitly says: "If an appropriate LOINC code does not exist, then the local code for this result SHALL be sent" (CONF:1198-19212). So expect LOINC, but be prepared for local/proprietary codes. Source: [STU1.1-V2] CONF:1198-19212.

**4.1.3 Result Observation `value` (Tier 2)**

| Attribute           | Constraint                  | Value                         | Source                      |
| ------------------- | --------------------------- | ----------------------------- | --------------------------- |
| `value`             | SHALL be present            | (CONF:1198-7143)              | [STU1.1-V2] Table 101       |
| `value/@xsi:type`   | Not constrained to one type | Could be PQ, CD, ST, CO, etc. | [STU1.1-V2] CONF:1198-7143  |
| If `@xsi:type="CD"` | SHOULD be                   | SNOMED CT                     | [STU1.1-V2] CONF:1198-32610 |
| If `@xsi:type="PQ"` | units SHALL be from         | UCUM                          | [STU1.1-V2] CONF:1198-31484 |

For code matching:

- If `value/@xsi:type="CD"` → check `value/@code` against SNOMED first (per SHOULD), then any other code system present
- If `value/@xsi:type="PQ"` or `"ST"` → no code to match; match on `observation/code` instead
- Source: [STU1.1-V2] CONF:1198-32610

> [!TIP]
> **Trigger codes on Result Observations**: In the eICR trigger code templates, the trigger can appear on EITHER `code` (test name, typically LOINC) OR `value` (organism/substance result, typically SNOMED) OR BOTH. The spec says "Either code or value or both shall contain a trigger code" (CONF:3284-300). The `@sdtc:valueSet="2.16.840.1.114222.4.11.7508"` marker tells you which element(s) are trigger codes. Source: [STU1.1-V2] CONF:3284-300.

> [!NOTE]
> **Organizer pruning strategy**: A Result Organizer SHALL contain at least one Result Observation (CONF:1198-7124). When filtering, you can keep the organizer but remove non-matching child observations, as long as at least one remains. If no observations match, remove the entire `<entry>` containing the organizer. Be aware that the organizer's own `code` might be a matching panel code even if individual observations don't match — decide your policy on this.

---

### 4.2 Encounters Section (LOINC `46240-8`)

**Entry structure (SHALL):**

```
section
 └─ entry [1..*]
     └─ encounter  [Encounter Activity]
         ├─ code  ← ENCOUNTER TYPE (Tier 2)
         └─ entryRelationship (MAY)
             └─ act  [Encounter Diagnosis]
                 └─ entryRelationship [@typeCode="SUBJ"]
                     └─ observation  [Problem Observation]
                         └─ value  ← DIAGNOSIS CODE (Tier 1, same as Problem Section)
```

**Encounter Activity `code` (Tier 2):**

| Attribute    | Constraint       | Value                                               | Source                     |
| ------------ | ---------------- | --------------------------------------------------- | -------------------------- |
| `code`       | SHALL be present | (CONF:1198-8714)                                    | [STU1.1-V2] Table 56       |
| `code/@code` | SHOULD be from   | EncounterTypeCode `2.16.840.1.113883.3.88.12.80.32` | [STU1.1-V2] CONF:1198-8714 |

The EncounterTypeCode value set includes CPT-4 E&M codes and SNOMED encounter types. The conformance is SHOULD, not SHALL. Source: [STU1.1-V2] Table 57.

**Encounter Diagnosis (Tier 1 — but the container is MAY):**

The Encounter Diagnosis itself is MAY on the Encounter Activity (CONF:1198-15492), but when present, the Problem Observation inside it follows the exact same Tier 1 rules as the Problem Section (value SHALL be SNOMED from the Problem value set). Source: [STU1.1-V2] Table 59, CONF:1198-14898.

> [!NOTE]
> **Do not remove the encounter itself** — the Encounters section provides critical context about the clinical visit. Your matching should focus on the Encounter Diagnosis entries within. If an Encounter Activity has no Encounter Diagnosis, or none of its diagnoses match, you likely still want to keep the encounter for contextual purposes.

---

### 4.3 Social History Section (LOINC `29762-2`)

This section is structurally heterogeneous. In STU 1.1 the document template requires Birth Sex (SHALL, CONF:3284-326/327) and Travel History (SHOULD, CONF:3284-334/335). The base C-CDA Social History section also allows various observation types (Smoking Status, Pregnancy, etc.) — all as MAY entries.

**Strategy:** Match child entries by their `templateId/@root`. Known roots get specific handling; unknown roots get skipped.

| Sub-observation | templateId @root                   | Code match point                      | Code system                                   | Source                           |
| --------------- | ---------------------------------- | ------------------------------------- | --------------------------------------------- | -------------------------------- |
| Birth Sex       | `2.16.840.1.113883.10.20.22.4.200` | `value/@code`                         | Administrative Gender `2.16.840.1.113883.5.1` | [STU1.1-V2] Birth Sex example    |
| Travel History  | `2.16.840.1.113883.10.20.15.2.3.1` | `act/code/@code` (always `420008001`) | SNOMED CT                                     | [STU1.1-V2] Table 116            |
| Smoking Status  | `2.16.840.1.113883.10.20.22.4.78`  | `value/@code`                         | SNOMED CT                                     | [STU1.1-V2] inherited from C-CDA |

> [!NOTE]
> **Social History is generally not a code-matching section for condition filtering.** Birth sex, smoking status, and travel history don't typically carry condition-specific SNOMED/ICD-10/LOINC codes that would match your configurations. You'll likely keep this section as-is rather than filtering its entries. The exception in STU 3.1.1 might be Exposure/Contact Information, which could be relevant to specific conditions.

---

### 4.4 Plan of Treatment Section (LOINC `18776-5`)

This section is MAY in STU 1.1 (CONF:3284-308). When present, it contains Planned Observations (lab test orders), which is where the Trigger Code Lab Test Order template lives.

**Entry structure (MAY entries):**

```
section
 └─ entry [0..*]
     └─ observation  [Planned Observation]
         └─ code  ← LAB ORDER CODE (Tier 2)
```

**Planned Observation `code` (Tier 2):**

| Attribute | Constraint       | Value                                     | Source               |
| --------- | ---------------- | ----------------------------------------- | -------------------- |
| `code`    | SHALL be present | Various — no single value set constrained | [STU1.1-V2] Table 82 |

The Planned Observation code system is not rigidly constrained in the base C-CDA template. When this observation is a Trigger Code Lab Test Order (templateId `15.2.3.4`), the `code` SHOULD come from the "Trigger code for laboratory test names" RCTC subset, which is typically LOINC. Detect via `@sdtc:valueSet="2.16.840.1.114222.4.11.7508"`. Source: [STU1.1-V2] Table 82 and Section 3.9.1.

---

## Part 5: Tier 3 Sections — No Structured Code Matching

These sections have no mandatory coded entries. Your pipeline cannot match individual entries against condition codes. Handle at the section level (keep or remove the whole section).

### 5.1 History of Present Illness (LOINC `10164-2`)

Narrative-only. The section constrains only `templateId`, `code`, `title`, and `text`. No entries are defined in the constraint table. Source: [STU1.1-V2] Table 31.

### 5.2 Reason for Visit (LOINC `29299-5`)

Narrative-only. Same pattern: only `templateId`, `code`, `title`, and `text`. No entries. Source: [STU1.1-V2] Table 45.

### 5.3 Chief Complaint (LOINC `10154-3`) — STU 3.1.1 only

Narrative-only in the standard C-CDA Chief Complaint section template. _[General CDA] — not independently verified against the 3.1.1 IG during this review, but consistent with the standard C-CDA pattern._

---

## Part 6: Trigger Code Detection (Cross-Section)

Trigger codes can appear in any section that has trigger-capable templates. The universal detection method works across all versions and sections.

**Universal trigger code marker (Tier 1):**

```
A code element is a trigger code if:
  @sdtc:valueSet = "2.16.840.1.114222.4.11.7508"
```

This works because every trigger code template in both STU 1.1 and STU 3.1.1 requires this marker when a trigger code is present (with the paired `@sdtc:valueSetVersion`). Source: [STU1.1-V2] CONF:3284-187 (Problem triggers), CONF:3284-290/302 (Result triggers).

**Where trigger codes appear by section:**

| Section           | Entry template                                             | Trigger element                               | Code system expected                         | Source                              |
| ----------------- | ---------------------------------------------------------- | --------------------------------------------- | -------------------------------------------- | ----------------------------------- |
| Problem           | Trigger Code Problem Observation (`.3.3`)                  | `observation/value`                           | SNOMED (from RCTC condition name subset)     | [STU1.1-V2] CONF:3284-176           |
| Results           | Trigger Code Result Observation (`.3.2`)                   | `observation/code` and/or `observation/value` | LOINC (test names) and/or SNOMED (organisms) | [STU1.1-V2] CONF:3284-305, 3284-303 |
| Plan of Treatment | Trigger Code Lab Test Order (`.3.4`)                       | `observation/code`                            | LOINC (test names)                           | [STU1.1-V2] Section 3.9.1           |
| Encounters        | via Encounter Diagnosis → Trigger Code Problem Observation | Same as Problem                               | SNOMED                                       | Same as Problem                     |

> [!NOTE]
> **STU 3.1.1 adds trigger templates for:** Medications (`.3.36`), Immunizations (`.3.38`), Procedures (`.3.44`, `.3.45`, `.3.46`), and Planned acts (`.3.41`, `.3.42`, `.3.43`). These follow the same `@sdtc:valueSet` marker pattern. If you use the universal marker detection approach, these new trigger types are automatically covered without code changes. Source: comparison document (cross-referenced against [STU3.1.1-V2] template index).

---

## Part 7: Code System Quick Reference

| Code System         | OID                         | Typical Usage                                                       |
| ------------------- | --------------------------- | ------------------------------------------------------------------- |
| SNOMED CT           | `2.16.840.1.113883.6.96`    | Problem/condition codes, result values (organisms), substance codes |
| ICD-10-CM           | `2.16.840.1.113883.6.90`    | Problem Observation `value/translation`                             |
| LOINC               | `2.16.840.1.113883.6.1`     | Section codes, result observation test codes, lab order codes       |
| RxNorm              | `2.16.840.1.113883.6.88`    | Medication codes                                                    |
| CVX                 | `2.16.840.1.113883.12.292`  | Immunization vaccine codes                                          |
| PHIN VS (CDC Local) | `2.16.840.1.114222.4.5.274` | RR determination codes (RRVS1, etc.)                                |
| PHIN Questions      | `2.16.840.1.114222.4.5.232` | RR organizer/observation fixed codes (RR1, RR11, etc.)              |
| CPT-4               | `2.16.840.1.113883.6.12`    | Encounter type codes                                                |

---

## Part 8: Entry Removal Strategy Notes

> [!TIP]
> **Narrative consistency**: CDA entries typically cross-reference the section's human-readable `<text>` via `text/reference/@value` pointing to a `#fragment` in the narrative. If you remove an entry, the corresponding narrative reference becomes a dangling pointer. Keith Boone's CDA Book emphasizes that the narrative and entries should be consistent. Options: (a) also clean up the narrative `<text>` when removing entries, (b) accept the dangling references as a practical trade-off, or (c) rebuild the narrative from the remaining entries. Source: [CDA Book] chapters on narrative/entry relationships.

> [!NOTE]
> **Organizer vs. observation removal**: For templates that nest observations inside organizers or acts (Problem Concern Act → Problem Observation, Result Organizer → Result Observation), decide your granularity: (a) remove individual child observations and keep the parent if any children remain, or (b) treat the parent + all children as a unit and keep/remove the whole thing based on whether ANY child matches. Option (a) is more precise but requires careful handling of the parent's `component` or `entryRelationship` count. Option (b) is simpler and safer.

> [!NOTE]
> **nullFlavor sections**: Several sections allow `@nullFlavor="NI"` on the section element itself (e.g., Problem Section CONF:1198-32864, Results Section CONF:1198-32875, Encounters CONF:1198-32815). When `@nullFlavor` is present, the section is asserting "no information" and entries are not required. Your parser should check for this and skip entry processing when found. Source: [STU1.1-V2] respective section constraint tables.

---

_Sources: CDAR2_IG_PHCASERPT_R2_STU1_1_2017JAN Vol2, CDAR2_IG_PHCASERPT_R2_STU3_1_1_Vol2_2022JUL_2024OCT, CDAR2_IG_PHCR_R2_RR_STU1_1_Vol2, and Keith Boone's "The CDA Book." Items marked [General CDA] are supplemented from general CDA implementation knowledge and should be independently verified against the relevant IG if precision is critical._
