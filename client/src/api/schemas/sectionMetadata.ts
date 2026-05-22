
/**
 * Utility class to help Orval ship these values to the frontend.

These sets of LOINC codes drive UI behavior in the eICR Sections
table and are sourced from refiner policy + the eICR specification.
Shipping them as literal-typed defaults means the frontend imports
real values rather than re-declaring them.
 */
export interface SectionMetadata {
  /**
     * @minItems 2
     * @maxItems 2
     */
  disabled_sections?: ['83910-0', '88085-6'];
  /**
     * @minItems 4
     * @maxItems 4
     */
  narrative_only_sections?: ['10154-3', '29299-5', '10164-2', '10187-3'];
}
