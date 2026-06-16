
/**
 * These sections are preserved intact in every refined document.
 *
 * They sit outside the normal refinement workflow not because the
 * refiner needs to protect them, but because we don't yet have a
 * real-world authoring contract to refine against:
 *
 * - Reportability Response Information (88085-6) is defined by the
 *   eICR STU 3.1.1 IG as a section the PHA populates after eICR
 *   receipt, as part of internal data integration -- not something
 *   the HCO authors at eICR generation time. It's sketched in the
 *   IG but is not part of eICRs flowing through AIMS today.
 *
 * - Emergency Outbreak Information (83910-0) has a defined section
 *   template and a deliberately generic Observation structure
 *   ("unknown until the time of the outbreak," per the IG). There
 *   is no settled EHR implementation pattern, and the next outbreak
 *   will likely shape how this section actually appears in
 *   production.
 *
 * Skipping is the easier path for now and produces Schematron-valid
 * output. We can revisit -- per section, independently -- if and
 * when either becomes something we actually see in real documents.
 *
 * The Enum is the single source of truth: used at runtime to derive
 * SECTION_PROCESSING_SKIP, and at the API boundary so Orval ships
 * the concrete LOINC codes to the frontend as const values rather
 * than as plain `string[]`.
 */
export type DisabledSection = typeof DisabledSection[keyof typeof DisabledSection];


export const DisabledSection = {
  '83910-0': '83910-0',
  '88085-6': '88085-6',
} as const;
