# eCR Refiner — Matching Engine Guide

This document explains how the matching engine works, how rules are structured and tiered, and--most importantly--how to debug a match failure. If an entry you expect to be retained is being dropped, or if you're adding coverage for a new section or implementation pattern (meaning something that isn't a part of the IG but shows up in production data), this is the right starting point.

## The two engines

Sections go through one of two matching engines, selected by the dispatcher in `section/__init__.py` based on whether the section's specification declares `entry_match_rules`:

1. **`entry_matching`**: IG-driven. Uses ordered rules with templateId-scoped xpaths to find specific coded elements within specific clinical statement templates. Supports intra-entry pruning (removing non-matching containers within a preserved entry) or whole-entry preservation depending on the rule. Used for Problems, Results, Immunizations, Vital Signs, Social History, Plan of Treatment, and others.

2. **`generic_matching`**: Unscoped fallback. Scans all `code`, `value`, and `translation` elements across all entries, preserves entries that contain a match, and does entry-level pruning only (no intra-entry pruning). Used for sections with no IG-verified structural rules — Chief Complaint, History of Present Illness, and others.

> [!IMPORTANT]
> It's important to understand **where** the matching engine can and cannot search when debugging whether or not it is working as expected. `generic_matching` will only look inside the elements **and** attributes listed in the script. Likewise, `entry_matching` will match in the locations that are added to the rules. If you need to match something that is not exactly standard; that is unique, it's important to understand the trade offs involved in creating a rule that looks in a very specific, non-standard way. We will develop this further below but it's important to highlight as we dig in to this more.

## How entry_matching evaluates rules

For each `<entry>` in a section, `_try_match_entry` in `entry_matching.py` walks the rule list in order. For each rule:

1. Run the rule's `code_xpath` against the entry tree
2. If any element with a `@code` attribute is found; **the rule claims the entry**, regardless of whether any code matched
3. Check each found element against the configured code set via `find_match`
4. If a match is found, record it and stop evaluating rules for this entry
5. If no match was found but candidates were found (step 2), **stop anyway** the entry is claimed, no subsequent rules run
6. If no candidates were found at all, continue to the next rule

Steps 2 and 5 together are **structural precedence**: the first rule that finds any code-bearing element at its xpath location owns the entry. This prevents lower-tier heuristic rules from firing when a higher-tier structural rule has already evaluated the IG-expected location.

If a rule has a `translation_xpath`, it is evaluated only when the primary `code_xpath` found candidates but produced no match — it extends the search within the same rule pass without releasing the claim.

> [!NOTE]
> In the future we may want to engineer a way to match more than one rule on a single `<entry>` but the complexity in pulling this off and understanding exactly **how** to correctly prune/preserve the right granular focus of clinical data for a reportable condition is a tough balance to strike. It isn't that this sort of option was deemed not important but that it was tricky to pull off when trying to establish this initial framework for matching.

## The tier system

Tiers describe how a rule was derived, not just its priority. When reading or writing rules, the tier tells you how much IG grounding the rule has. The canonical definition lives at the top of `specification/entry_match_rules.py` — this section summarizes it.

### T1: SHALL

The rule targets a specific `templateId` and a specific element that the IG says SHALL carry the condition-relevant code. There is a CONF citation in the comment backing the xpath choice. If this rule fires, the match is directly IG-mandated. If a sender follows the spec, this rule matches.

Examples: SNOMED on Problem Observation `value` (CONF:1098-31526), LOINC on Vital Sign Observation `code` (CONF:1098-7301), CVX on `manufacturedMaterial/code` (CONF:1098-9007).

### T2: SHOULD/MAY

The rule covers a pattern the IG permits but does not require; a SHOULD or MAY binding. The code may appear in a translation element, an alternate code location, or a secondary code system. The rule is still IG-grounded and carries a CONF citation, but conformant senders are not required to populate this path.

Examples: LOINC in `observation/code/translation` on Results (SHOULD), SNOMED organism code on Result Observation `value` with `sdtc:valueSet` guard (SHOULD), ICD-10 in `value/translation` on Problems (MAY, CONF:1198-16750).

### T3: Heuristic

Not IG-conformant. Observed in real EHR output but not described by the spec. No CONF citation. Each T3 rule carries a note in its comment describing what real-world pattern it was written for. T3 rules exist to accommodate vendor variance, not to cover spec patterns.

Examples: ICD-10 as primary on `observation/value` with SNOMED in translation (reversed coding, opposite of the IG's preferred order), Social History broad union xpaths (structural diversity makes templateId-scoped rules harmful).

Knowing the tier of an existing rule tells you whether a match failure is a spec gap (the IG doesn't describe this shape -> T3 candidate), a SHOULD/MAY gap (the IG permits it but the T1 rule doesn't cover it -> T2 candidate), or a configuration gap (the code isn't in the jurisdiction's configured set -> add it to the condition's configuration as a custom code).

## Debugging a match failure

When an entry you expect to be retained is being dropped, work through this in order.

### Step 1: Find the element in the source XML

Open the original eICR and find the entry. Identify:

- What element carries the code you think should match (`observation/code`, `observation/value`, `act/code`, `manufacturedMaterial/code`, etc.)
- What the actual `@code` value is
- What `@codeSystem` OID is declared on that element
- What `templateId` is on the containing clinical statement

### Step 2: Check whether the code is configured

There are three ways to check:

**`just db check-code` — quickest:**

```bash
just db check-code "COVID-19" "5.0.0" "snomed_codes" "260373001"
```

This runs a targeted query against the condition's grouper and shows whether the code is present and what display name it has. Swap the system name (`snomed_codes`, `loinc_codes`, `icd10_codes`, `rxnorm_codes`, `cvx_codes`) to match the element's code system.

**Webapp configuration screen**; useful if you need to browse all configured codes for a jurisdiction without knowing the specific code in advance.

**CSV export**: the webapp can export the active configuration for a jurisdiction. Useful for bulk inspection or sharing with a subject matter expert who needs to review the full code set.

If the code is not configured, the entry correctly won't match. This is a **configuration issue**, not a rules issue; then the recommendation would be to add the code as a custom code to the condition's configuration.

### Step 3: Find the rule that should cover this entry

Open `specification/entry_match_rules.py` and find the `_*_MATCH_RULES` list for the section (identified by its LOINC code). Find the rule whose `code_xpath` targets the element you identified in step 1. Check:

- Does the xpath's `templateId` filter match the `templateId` on the entry's clinical statement? (If the entry uses a different extension or a different root, the filter won't match.)
- Does `code_system_oid` match the `@codeSystem` on the element, or is it `None` (accept any)?
- Is there a `translation_xpath` that also checks a secondary location?

If no rule covers the entry's structural shape, skip to [Adding a new rule](#adding-a-new-rule).

### Step 4: Check for structural precedence blocking

If a rule exists but the entry still doesn't match, the most likely cause is that a higher-rule is claiming the entry before yours runs.

Ask: does the entry contain any element with a `@code` attribute that matches an **earlier** rule's `code_xpath`? If yes, that earlier rule claims the entry and your rule never evaluates it.

Common blocking scenarios:

| Situation                                                                                       | Why it blocks                                                                                                     |
| ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Entry has `ASSERTION` on `observation/code`, configured code is on `observation/value`          | A rule targeting `observation/code` finds `ASSERTION`, claims the entry, translation branch doesn't reach `value` |
| Entry has a local OID code on `observation/code`, configured code is on `observation/value`     | Same — `observation/code` has a candidate, entry claimed                                                          |
| Jurisdiction configures a LOINC panel code (`21843-8`) but the rule targets `observation/value` | Rule finds value candidates, claims, panel code on `observation/code` never evaluated                             |

Fixes for blocking:

- Add a `translation_xpath` to the claiming rule pointing at the secondary location (e.g. `observation/value`). This extends the claiming rule's search to cover both locations before giving up (this is a great strategy to try and get two rules working in the same rule in a lot of ways).
- If the claiming rule is lower-tier than yours, reorder the rules.
- If both rules cover the same structural location, collapse them into one rule with a union xpath.

> [!TIP]
> An example of this is with the Social History seciton; there are patterns that exist in that section that make it difficult to prune/filter the **right** clinical data. We had a lot of T2 and T3 rules that were fighting each other and the fix was simply to collapse some of these into two T3 heuristic based rules where one has a `translation_xpath` and the other handles a case where the first rule wouldn't claim but the translation level rule would. The rules also leverage `preserve_whole_entry=True`, which will not aggressively prune and preserve the whole `<entry>`. This is helpful in this section because there's a lot of patterns that can show up in fairly shallowly nested patterns--this was a choice that struck the right balance for the time being. So you will sometimes need to try and strike the right balance while iteratively trying a few different things and rerunning the refinement with custom codes for that section to get the right output.

### Step 5: Look at the IG

If the rule is missing or wrong, check the IG volume for the section:

- What templateId does the IG define for this entry type?
- What element does the IG say SHALL or SHOULD carry the condition-relevant code?
- Is there a CONF citation you can reference in the rule comment?

### Step 6: Check that the rule is wired into the catalog

New `_*_MATCH_RULES` lists need to be connected in `specification/catalog.py`. Verify that the section's `SectionSpecification` references your rule list:

```python
SectionSpecification(
    loinc_code="11450-4",
    ...
    entry_match_rules=_PROBLEM_MATCH_RULES,
)
```

If `entry_match_rules` is absent or `None`, `process_section` routes to `generic_matching` instead of `entry_matching`.

## Adding a new rule

### Decide the tier

**T1** if:

- The IG has a SHALL binding for this element and `templateId`
- You can cite a CONF number
- If a sender follows the spec, this rule matches

**T2** if:

- The IG has a SHOULD or MAY binding for this pattern--it's permitted but not required
- You can still cite a CONF number
- Examples: a code in `translation`, an alternate code location, a secondary code system the IG explicitly allows

**T3** if:

- The pattern is not described by the IG at all--it's observed in real EHR output but has no spec grounding
- Document what real-world pattern the rule was written for in the comment (e.g. "Epic sends RxNorm as primary instead of CVX")
- Or: the section has no reliable structural anchor and templateId-scoped rules cause more structural precedence problems than they solve--document the full rationale

### Place the rule correctly

Rules are evaluated in list order. T1 rules go first, T2 next, T3 last. Within a tier, more specific rules (narrower `templateId` scope) go before less specific ones.

If your rule is a fallback that should only fire when no structured rule matched, ensure all higher-tier rules come before it in the list.

### Choose the right preservation strategy

- `prune_container_xpath`: use when the match targets a specific container (e.g. a `component` within an `organizer`) and non-matching containers in the same entry should be removed. The match is surgically precise. Used for Results (individual lab observations) and Vital Signs.

- `preserve_whole_entry=True`: use when the clinical context lives in `participant` and `entryRelationship` chains that path-based pruning would strip. The entire entry is kept intact regardless of what else is in it. Used for Immunizations (reaction chains), Social History (travel destinations, employer details, exposure agents), Medications, and Procedures. **When in doubt, use `preserve_whole_entry=True`**; intra-entry pruning on sections where context chains matter will produce valid CDA that silently loses clinical meaning.

The default path-based pruner in `generic_matching` walks ancestor chains from the matched element to the entry root and preserves everything on those paths plus coding-cluster siblings (sibling `code`/`value`/`translation` elements on the same parent). Use this when the match is on a specific element and the surrounding structural metadata (`statusCode`, `effectiveTime`, `id`) should survive but unrelated subtrees should not.

### Common rule patterns

| Sender pattern                                                                  | Rule shape                                                                                      |
| ------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| IG-conformant: standard code on expected element                                | T1, `code_xpath` targets element, `code_system_oid` set to expected OID                         |
| Standard code in `translation`, local primary (IG permits via SHOULD/MAY)       | T2, add `translation_xpath` to T1 rule pointing at `element/translation`                        |
| nullFlavor primary or reversed coding--not IG-described, observed in EHR output | T3, `translation_xpath` on same rule, `code_system_oid=None`, document the vendor pattern       |
| `ASSERTION` on `observation/code`, clinical code on `observation/value`         | Add `translation_xpath=".//hl7:observation/hl7:value"` to the rule targeting `observation/code` |
| Section too heterogeneous for structural rules                                  | T3 with broad union xpath, `preserve_whole_entry=True`, full rationale in comment               |

---

## Reference: key files

| File                                 | Purpose                                                                          |
| ------------------------------------ | -------------------------------------------------------------------------------- |
| `specification/entry_match_rules.py` | All `_*_MATCH_RULES` lists with inline CONF citations and tier rationale         |
| `specification/catalog.py`           | Wires rule lists into `SectionSpecification` objects; the dispatcher reads these |
| `specification/loader.py`            | Detects eICR version from document; assembles the full spec for a version        |
| `section/entry_matching.py`          | Rule evaluation engine--`_try_match_entry` is the core loop                      |
| `section/generic_matching.py`        | Unscoped fallback engine                                                         |
| `section/__init__.py`                | Dispatcher--picks engine based on whether `entry_match_rules` is set             |
| `model.py`                           | `EntryMatchRule` dataclass — field definitions and semantics                     |
