
/**
 * These sections are preserved intact in every refined document, even if a jurisdiction has not configured them.

They exist outside the normal refinement workflow because their content is either public-health
infrastructure (outbreak information) or downstream routing metadata
(reportability response content) that jurisdictions expect to see
untouched in the refined output. In the future we may decide to implement new ways to handle these sections
but for now skipping them is easier and produces valid (Schematron-valid)
output. The Literal-typed tuple alias below is the single source of truth: it is
used both at runtime (to derive SECTION_PROCESSING_SKIP) and at the API
boundary (so Orval ships the concrete LOINC codes to the frontend as
const values rather than as plain `string[]`).
 */
export type DisabledSection = typeof DisabledSection[keyof typeof DisabledSection];


export const DisabledSection = {
  '83910-0': '83910-0',
  '88085-6': '88085-6',
} as const;
