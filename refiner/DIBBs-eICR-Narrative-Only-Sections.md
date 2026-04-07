# Narrative-Only Sections: Retain or Remove (No Refine)

## Decision

Four eICR sections are configured with only two actions — `"retain"` or `"remove"` — and are excluded from entry-level code matching. The `"refine"` action is not offered for these sections because there are no structured entries to filter against.

| Section                    | LOINC   | Template OID                         |
| -------------------------- | ------- | ------------------------------------ |
| Chief Complaint            | 10154-3 | `1.3.6.1.4.1.19376.1.5.3.1.1.13.2.1` |
| Reason for Visit           | 29299-5 | `2.16.840.1.113883.10.20.22.2.12`    |
| History of Present Illness | 10164-2 | `1.3.6.1.4.1.19376.1.5.3.1.3.4`      |
| Review of Systems          | 10187-3 | `1.3.6.1.4.1.19376.1.5.3.1.3.18`     |

## Rationale

### The IGs define no entries for these sections

In both the eICR STU 1.1 (Vol 2, §2.2–2.7) and eICR STU 3.1.1 (Vol 2, §2.3, 2.7, 2.16, 2.19), the constraints overview tables for these sections list only `templateId`, `code`, `title`, and `text` — all at SHALL. No `entry` element appears at any conformance level (SHALL, SHOULD, or MAY). The "Contains:" column in each section's context table is empty, confirming no entry-level templates are referenced.

### The schematron validates no entries in these sections

The STU 3.1.1 schematron (`CDAR2_IG_PHCASERPT_R2_STU3_1_1_SCHEMATRON.sch`) confirms this. For each of these four sections, the error-level rules assert only:

- `count(cda:templateId[...])=1`
- `count(cda:code)=1`
- `cda:code[@code='...']`
- `count(cda:title)=1`
- `count(cda:text)=1`

The warning-level rules are no-ops (`<sch:assert test=".">` — always passes). There are zero assertions referencing `cda:entry` in any of these patterns.

By contrast, sections like Encounters (entries required) explicitly enforce entry presence and template conformance:

```xml
<!-- From the Encounters Section (entries required) schematron rule -->
<sch:assert id="a-1198-8709-c"
  test="(cda:entry/cda:encounter/cda:templateId[
    @root='2.16.840.1.113883.10.20.22.4.49'][@extension='2015-08-01']
    or @nullFlavor) and not(cda:entry and @nullFlavor)">
```

Nothing analogous exists for the four narrative-only sections.

### Open templates permit but do not expect entries

All four templates are declared `(open)`, meaning a conformant document _could_ include additional content (including entries) beyond what the template constrains. However, any such entries would be:

- Outside the IG's design intent
- Not validated by the schematron
- Not conformant to any eICR-defined entry template within that section context

This is consistent with the CDA R2 layered validation model: the XSD enforces structural grammar, schematron enforces template-level conformance on top of that. When schematron has no rules for entries in a given section context, those entries exist in a validation blind spot (see Keith Boone, _The CDA Book_, Ch. 15 — sections on the `entry` association class and the distinction between Level 2 and Level 3 CDA conformance).

## Implication for the Refiner

The `"refine"` action depends on entry-level code matching (`EntryMatchRule` evaluation) to selectively retain condition-relevant entries. For sections with no IG-defined entries, there is nothing to match against — the only meaningful content is the narrative block, which is indivisible from the refiner's perspective. Offering `"refine"` for these sections would be misleading: it implies entry-level filtering that cannot occur.

The section catalog in `specification.py` encodes this by omitting `entry_match_rules` for these four sections, which restricts the available actions to `"retain"` or `"remove"` at the configuration layer.

## References

- eICR STU 1.1, Volume 2 (2017 JAN): §2.2 (HPI), §2.7 (Reason for Visit), §1.1.3.6–1.1.3.7 (document-level section requirements)
- eICR STU 3.1.1, Volume 2 (2022 JUL / 2024 OCT): §2.3 (Chief Complaint), §2.7 (HPI), §2.16 (Reason for Visit), §2.19 (Review of Systems)
- STU 3.1.1 Schematron: patterns `p-urn-oid-1.3.6.1.4.1.19376.1.5.3.1.1.13.2.1-errors`, `p-urn-oid-2.16.840.1.113883.10.20.22.2.12-errors`, `p-urn-oid-1.3.6.1.4.1.19376.1.5.3.1.3.4-errors`, `p-urn-oid-1.3.6.1.4.1.19376.1.5.3.1.3.18-errors`
- Keith Boone, _The CDA Book_ (Springer), Chapter 15: The CDA Body — §15.2 (Structured Narrative / Section class), §15.3 (The Narrative Block)
