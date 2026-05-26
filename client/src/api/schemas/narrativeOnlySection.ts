
/**
 * These sections have no entry match rules in the eICR specification.

They are conveyed via the narrative block only. Configuring them for
"refine" is meaningless (there is nothing to match against), so the
UI disables the refine toggle for them and the refinement plan
normalizes "refine" -> "retain" for these codes (see refine.py).
The Enum values remain the single source of truth shipped to the frontend.
A unit test guards that this enum stays in sync with the spec catalog
(every code listed here has has_match_rules=False in the catalog, and
every catalog section with has_match_rules=False is listed here).
 */
export type NarrativeOnlySection = typeof NarrativeOnlySection[keyof typeof NarrativeOnlySection];


export const NarrativeOnlySection = {
  '10154-3': '10154-3',
  '29299-5': '29299-5',
  '10164-2': '10164-2',
  '10187-3': '10187-3',
} as const;
