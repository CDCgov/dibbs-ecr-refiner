# 13. Zero-Code-Set Refinement

Date: 2026-07-22

## Status

Proposed

## Context and Problem Statement

Currently, the refinement process requires associated code sets. It is
impossible to perform refinement using ONLY custom codes without at least one
associated code set (primary).

The system relies on fragile coupling: `condition.display_name == config.name`
to identify the initial condition. This coupling causes a critical regression:
removing the default code set triggers a `ValueError` in the refinement pipeline,
resulting in a 400 error. TES trigger detection remains functional (independent
of code sets), but refinement fails when no initial condition exists.

## Decision Drivers

- Support refinement workflows that use only custom codes enabling jurisdictions
  to include only the specific codes for conditions they need in any given
  configuration
- Minimize risk and disruption to existing functionality
- Enable quick implementation while maintaining data integrity
- Decouple configuration identity from mapping logic (initial condition)
- Ensure a predictable 'unrefined passthrough' behavior for zero-code-set
  configurations

## Considered Options

### 1. Prototype approach (Structural Change)

- Modify backend to allow configurations without a primary condition.
- Move from name-matching to an explicit, optional `primary_condition_id`
  pointer.
- Update API/Database constraints to make primary conditions optional.
- Update UI to handle empty state for code sets.
- **Unrefined Passthrough**: If no primary condition exists, the system performs
  a clean passthrough.
- **UI Warning**: Warn users before activating a configuration with no mapping
  logic.
- **RSG Code Fix**: Decouple RSG code resolution from the primary condition.
  Implement a fallback mechanism so custom codes can leverage RSG mappings
  even without a primary condition. This requires modifying the RSG lookup
  logic to operate independently of `primary_condition_id`.

**Pros**: Cleanest data model for the requirement. Explicit decoupling of
configuration identity from mapping logic.

**Cons**: Requires schema/API changes and more extensive testing of constraints.
Need to update `seed_db.py` to ensure deletions persist across redeploys.

### 2. Toggle approach (Soft Disable)

- **Design**: Add a boolean flag `ignore_associated_sets` to the configuration
  model. Add a corresponding UI toggle in the Config Builder to enable/disable
  this flag.
- **Behavior**: When enabled, the refinement pipeline bypasses all associated
  code set mapping logic and processes only custom codes. The system performs a
  clean passthrough for custom codes without applying any code set mappings.
- **Unrefined Passthrough**: If the toggle is enabled, the system processes only
  custom codes, ignoring any associated code sets entirely.

**Pros**: Low risk, no schema changes to primary condition requirements, easy to
revert. Does not require changes to existing database constraints or API
endpoints.

**Cons**:

- **State Dissonance**: Creates a "ghost state" where the database indicates
  associated code sets exist, but the pipeline ignores them, making debugging
  and auditing more difficult.
- **UI Confusion**: Users may find it contradictory to see associated code sets
  listed in the UI while a toggle indicates they are being ignored.
- **Constraint Dependency**: Unlike the Prototype approach, this may still
  require a "dummy" primary condition to satisfy existing database constraints
  if the schema is not relaxed.
- Does not provide the explicit decoupling of the Prototype approach.

**UX Mitigations**:

- **Visual Cues**: Implement visual dimming (e.g., reduced opacity/grayscale)
  for the associated code sets table when the toggle is active to signal
  inactivity.
- **Status Indicators**: Add "Bypassed" or "Ignored" badges to associated sets
  when the toggle is active.
- **Contextual Alerts**: Display a prominent banner/alert in the Code Sets
  section informing the user that associated sets are disabled and only custom
  codes are being used.
- **Interaction Constraints**: Provide clear feedback (e.g., tooltips or
  disabled states) on association buttons when the toggle is active to explain
  why modifications may be restricted or ignored.

These mitigations directly address the cons:

- **State Dissonance**: Visual cues and status indicators make the inactive
  state explicit, reducing ambiguity during debugging and auditing.
- **UI Confusion**: Contextual alerts and interaction constraints clarify why
  associated sets are visible but not active, eliminating the contradictory
  appearance.

### 3. Do Nothing

- Maintain current behavior.

**Pros**: No effort.

**Cons**: Feature remains impossible.

## Decision Outcome

> [!IMPORTANT]
> We have not decided on a direction yet. Once we have, we will update this
> section accordingly. This document is mostly to document all of the findings
> from [CDCgov/dibbs-ecr-refiner#1525](https://github.com/CDCGov/dibbs-ecr-refiner/issues/1525).

## Appendix

### Technical Findings

#### Refinement Pipeline Regression (The 400 Error)

The critical regression occurs in the refinement pipeline's error handling
chain:

1. `create_eicr_refinement_plan` calls
   `get_condition_by_display_name_db(config.name)` to resolve the initial
   condition.
2. If this returns `None` (no conditions associated), a `ValueError` is raised
   with the message "Configuration has no initial condition."
3. `refine_eicr` catches this `ValueError` and converts it into an
   `HTTPException(400)`.

This creates a critical regression where removing the default code set makes the
entire configuration unusable for refinement. Every refinement attempt for a
zero-code-set configuration returns a 400 error.

#### Fragile Coupling

The system relies on `condition.display_name == config.name` to identify the
"initial condition." This coupling is problematic because:

- Changes to the configuration name would break the link to the initial
  condition.
- The name-matching approach is implicit and brittle; it assumes the
  configuration name always matches a condition's display name.
- This creates a hidden dependency between configuration identity and mapping
  logic.

#### TES Trigger Independence

TES trigger detection is independent of associated code sets. It is driven by:

- `detect_eicr_version`: Reads the eICR document's schema version from the XML.
- `load_spec`: Fetches specifications by that version.

This means triggers still evaluate even when no TES condition is attached to the
configuration. The refinement pipeline can process sections and apply rules
regardless of whether code sets exist.

#### Database Integrity

The `is_config_valid_to_insert_db` function checks for the presence of
**sections**, not **conditions**. Specifically:

```python
async def is_config_valid_to_insert_db(
    condition_canonical_url: str, jurisdiction_id: str, db: AsyncDatabaseConnection
) -> bool:
    """
    Query the database to check if a configuration can be created. If a config for a condition already exists, returns False.
    """
    query = """
        SELECT c.id
        FROM configurations c
        JOIN configurations_conditions cc ON cc.configuration_id = c.id AND cc.is_primary = true
        JOIN conditions cond ON cond.id = cc.condition_id
        WHERE cond.canonical_url = %s
        AND c.jurisdiction_id = %s
        AND c.status = 'draft'
        """
```

The query checks for existing configurations by condition canonical URL, but
there is no rule requiring at least one condition. A zero-code-set configuration
does not violate database insertion rules.

#### Persistence Gotcha (Seeding)

The `seed_db.py` behavior presents a persistence challenge:

- `seed_database()` truncates the `configurations_conditions` table with
  `CASCADE` before reloading static data.
- `load_static_data()` then reloads all seeded conditions and their
  relationships.
- This means user-deleted code sets would return on every reseed/redeploy.

Allowing removal of code sets is meaningless unless seeding is also modified to
preserve user deletions.

#### API Guard

The specific 409 conflict guard in `codesets.py` previously blocked the removal
of the condition matching the configuration name:

```python
if condition.display_name == config.name:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Cannot remove initial condition.",
    )
```

This guard was removed in commit `98889d42` to allow deletion of the primary
condition, but the refinement pipeline regression (the 400 error) remained as
the critical blocker.

#### RSG Code Dependency

RSG code lookup currently relies on the primary condition ID. The refinement
pipeline resolves RSG mappings by first identifying the primary condition, then
looking up associated RSG codes for that condition. In a zero-code-set
configuration, this lookup fails because there is no primary condition to anchor
the RSG mapping resolution.

This results in a loss of RSG mapping even when custom codes are present that
could benefit from RSG resolution. The dependency creates a blocker: without a
primary condition, custom codes cannot leverage RSG mappings, limiting the
utility of zero-code-set configurations.

#### API Contract Change

The `GetConfigurationResponse` schema was modified to support zero-code-set
configurations by making `condition_id` and `condition_canonical_url` optional:

- `condition_id`: Changed from `UUID` to `UUID | None`
- `condition_canonical_url`: Changed from `str` to `str | None`

This requires updated null-handling in the frontend, particularly in:

- Code Set Builder views that display condition metadata
- Configuration detail pages that reference the condition canonical URL
- Any component that constructs URLs or performs lookups using these fields

#### Passthrough Mechanism

The "unrefined passthrough" is not a separate mode or configuration flag. It is
the natural result of the refinement pipeline skipping all mapping loops when no
primary condition or associated code sets are present.

The pipeline flow:

1. Attempt to resolve primary condition → returns `None`
2. Skip all code set mapping loops (no conditions to iterate)
3. Process custom codes through TES triggers only
4. Return eICR with no code set mappings applied

This behavior is implicit and requires no special handling in the pipeline.
