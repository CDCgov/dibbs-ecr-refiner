# 5. `displayName` Enrichment

Date: 2026-02-18

## Status

Proposed

## Context and Problem Statement

As documented in issue [#802](https://github.com/CDCgov/dibbs-ecr-refiner/issues/802), eICRs from certain EHR systems are often missing the `displayName` attribute on coded elements (e.g., `<code code="64572001" ... />`). While the `code` is present, the human-readable `displayName` is not, which is a critical component for downstream public health systems that rely on this text for data interpretation and display.

The refiner has access to the correct `displayName` for these codes through its connection to the database (via condition data and user-provided custom codes). The challenge is to efficiently and reliably enrich the refined eICR XML by adding these missing `displayName` attributes to the appropriate elements before the final output is generated.

This RFC evaluates strategies to solve this enrichment problem, while also considering how the chosen solution can support future enhancements, specifically the generation of more contextually-rich narrative (`<text>`) tables within refined sections.

## Decision Drivers

- **Data Completeness:** The primary driver is to produce a refined eICR that is as complete as possible to maximize its utility for jurisdictions.
- **Maintainability:** The solution should not significantly increase the complexity of the core refinement logic, making it hard to maintain or extend.
- **Clarity and Testability:** The chosen approach should be easy to reason about and isolate for unit testing.
- **Future-Proofing:** The solution should align with long-term goals for the service, such as improving narrative generation, rather than being a short-term patch.

## Considered Options

### Option 1: Post-Processing Enrichment Pass

This approach adds a final, distinct step after the main refinement logic is complete.

- **Logic**: After `refine_eicr` filters the document but before the XML is converted to a string, a new function `enrich_display_names(xml_root, code_map)` would traverse the processed XML tree. It would find all `<code>`, `<value>`, and `<translation>` elements missing a `displayName` and add it if the corresponding code exists in the `code_map` passed down from the orchestration layer.

| Pros                                                                                  | Cons                                                                                           |
| ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **Low Coupling**: Minimally invasive; keeps enrichment separate from filtering logic. | **Potentially Inefficient**: Requires a second full traversal of the structured body.          |
| **Easy to Reason About**: A simple, understandable, and final clean-up step.          | **Does Not Support Other Features**: Provides no foundation for improving `<text>` generation. |
| **Small Change Magnitude**: Requires one new function and a single call to it.        | **Risk of Over-enrichment**: Could modify sections intended to be retained without changes.    |

### Option 2: Data-Driven Enrichment During Extraction (Chosen)

This approach integrates enrichment into the existing data extraction pipeline that generates the `<text>` element.

- **Logic**: The `_extract_clinical_data` function in `process_eicr.py` would be enhanced. As it reads a clinical element to prepare data for the summary table, it would also check for a missing `displayName`. If absent, it would look up the code in a provided map and **write the `displayName` back to the XML element directly**. This requires evolving the function to be a structured "read-and-write" process.

| Pros                                                                                                                                                                            | Cons                                                                                                          |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Targeted and Efficient**: Only modifies elements confirmed to be relevant and kept.                                                                                           | **Higher Coupling**: Expands the responsibility of the extraction function from reading to writing.           |
| **Foundation for Future Features**: **Crucially, this approach provides the architecture needed for section-specific `<text>` table generation.**                               | **Requires Refactoring**: The existing extraction logic would need to be evolved into a more robust pipeline. |
| **Solves Both Problems Together**: By extracting into a structured model first, both enrichment and improved `<text>` generation can be achieved in a single, unified workflow. |                                                                                                               |

### Option 3: Global "Fix-Up" on XML Parsing

This approach uses advanced `lxml` features to modify the XML during the initial parsing step.

- **Logic**: A custom `lxml` parser would be created. During parsing, a callback target would inspect each element. If it's a `<code>` element missing a `displayName`, it would add it on the fly. All subsequent logic would operate on an already-enriched XML tree.

| Pros                                                                   | Cons                                                                                   |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| **Completely Decoupled**: Refinement logic is unaware of this process. | **High Complexity**: `lxml` parser customization is advanced and difficult to debug.   |
|                                                                        | **Overkill**: A very powerful and complex solution for a relatively contained problem. |
|                                                                        | **Large Change Magnitude**: A fundamental change to the XML parsing pipeline.          |

## Decision Outcome

**Option 2 (Data-Driven Enrichment During Extraction) is selected.**

While Option 1 presents a quicker, more isolated fix for the `displayName` problem, it is a tactical solution that incurs technical debt. It solves today's problem but ignores the closely related and equally important need for improved narrative generation in the `<text>` element.

Option 2 is the more strategic choice because it establishes a single, robust architecture that solves both problems. By creating a pipeline that extracts clinical data into structured Python objects (e.g., `ResultFinding`, `MedicationFinding`), we gain a clean, intermediate representation. This model can be enriched with the `displayName` from our database and can then be used to generate a contextually-aware, section-specific HTML table for the `<text>` element.

### Key Implementation Details: Passing the Code Map

To enable enrichment, the `displayName` information, which is currently discarded during terminology processing, must be preserved and passed down to the refinement logic. This will be achieved through the following model changes:

1. **Modify `ProcessedConfiguration`:** The `ProcessedConfiguration.from_payload` method in `terminology.py` will be updated. In addition to creating the `codes: set[str]`, it will also create a new `code_display_map: dict[str, str]` attribute. This map will be populated from the `DbCondition` and `DbConfiguration` custom code objects.

2. **Modify `EICRRefinementPlan`:** The `EICRRefinementPlan` object in `ecr/models.py` will be extended to include the `code_display_map`. The `create_eicr_refinement_plan` function will be responsible for passing this map from the `ProcessedConfiguration` into the plan.

3. **Update Function Signatures:** The `refine_eicr` and `process_section` functions will be updated to accept this map (likely via the plan object) so it is available where the XML enrichment occurs.

> [!NOTE]
> Regardless of the solution selected, this architectural change is a prerequisite for the chosen solution to be possible by providing the necessary data to the core refinement functions.

### Implementation Strategy: Together or Sequentially?

It is highly recommended to implement both `displayName` enrichment and the initial framework for section-specific `<text>` generation **together**.

The core task required for both features is the same: **refactoring the data extraction logic to be model-driven.** Building the infrastructure for one without considering the other would be inefficient and lead to rework.

The proposed sequence is:

1. Refactor `_extract_clinical_data` and its callers to support a model-driven approach where XML elements are parsed into structured Python objects.
2. During this extraction, implement the `displayName` enrichment logic.
3. Simultaneously, modify the `<text>` generation logic (`_create_or_update_text_element`) to use these new structured objects to build the summary table. Initially, this can be for one or two key sections (e.g., Results) to prove the pattern.

This unified approach ensures we build the right foundation from the start, delivering immediate value with `displayName` enrichment while creating a clear, scalable path for all future `<text>` generation enhancements.

> [!NOTE]
> I can understand there being pushback to doing both of these together. The first question I thought I would get is "can we just implement a solve for the `displayName` issue **now** and then work on the narrative section later?". I'll add my response to that question below:

We absolutely could implement a simple `displayName` fix now and push the `<text>` narrative work to later. The quickest way to do that would be with a simple post-processing pass that runs after refinement, finds the missing attributes, and fills them in.

However, choosing that path would be a deliberate decision to accept throwaway work.

Here’s why doing them together is the more efficient and responsible engineering choice:

- **Both features require the exact same information**. To correctly generate a section-specific `<text>` table for the "Results" section, we need to extract the test name (`displayName`), the code, the value, and the units. To enrich a missing `displayName` in that same section, we also need to look at the code and use our mapping to find its name. The context needed is identical.

- **Doing them separately means building two different mechanisms to do the same thing**.
  - **Path A (Separate)**: First, we'd build a "quick" mechanism to traverse the XML and fix `displayNames`. Later, when we decide to improve the `<text>` tables, we would have to build a second, more sophisticated mechanism to traverse the XML again, extract the structured data (like test values), and then build the table. The first mechanism becomes instantly obsolete.
  - **Path B (Together)**: We build the sophisticated data extraction mechanism once. As it pulls the structured data out of the XML to prepare for `<text>` generation, it's trivial to perform the `displayName` enrichment at the same time.

> Essentially, the "quick fix" for `displayNames` is a temporary patch that doesn't align with our long-term architectural needs for this part of the codebase. By building the proper data extraction pipeline now (Option 2), we're not just solving the `displayName` issue; we are building the permanent foundation required for the `<text>` enhancement.

So, the answer to "Can we do it separately?" is "Yes, but it would be inefficient." We would be spending time and resources developing, testing, and deploying a feature that we know from the outset we are going to replace.

Doing them together isn't about making the task bigger; it's about doing it right the first time.

## Consequences

**Positive:**

- Solves the immediate `displayName` problem in a robust way.
- Provides a clear and scalable architecture for generating rich, section-specific `<text>` elements.
- Reduces future rework by building the correct foundation now.
- Improves testability by separating messy XML parsing from clean data model manipulation.

**Negative:**

- Requires a more significant upfront refactoring effort compared to the "quick fix" in Option 1.
- Increases the complexity of the data extraction pipeline, though this is managed by using clear, strongly-typed data models.

## Appendix

### Related Tickets

- **Spike**: [#802](https://github.com/CDCgov/dibbs-ecr-refiner/issues/802)
