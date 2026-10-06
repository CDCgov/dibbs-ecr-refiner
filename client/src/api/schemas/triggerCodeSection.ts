
/**
 * These sections can carry an eICR trigger code template.
 *
 * The eICR IG defines trigger code templates for these sections, so a
 * trigger code — the coded evidence of *why* the document was
 * generated — can appear in any of them. Removing a section strips
 * every `<entry>` it holds and marks it `nullFlavor="NI"` (see
 * `create_minimal_section`), so a jurisdiction that turned all of
 * these off would emit a document with no trigger codes anywhere and
 * fail Schematron validation.
 *
 * In practice this is unlikely: nearly all RCTC codes from the eRSD
 * are carried in the reporting specification groupers, and the
 * additional context groupers widen that further, so a configuration
 * would normally match the trigger code and keep the section. This
 * policy exists to close the foot-gun, not because we expect
 * jurisdictions to walk into it.
 *
 * The refiner therefore forces `include=True` for these sections.
 * Every other setting stays under jurisdiction control — coded data
 * may still be refined or retained, and the narrative may be
 * retained, removed, kept on match, or reconstructed.
 *
 * Membership is IG-derived, not a judgement call: the codes here are
 * the union of `specification.get_trigger_code_sections()` across
 * every supported eICR version. The union matters because a
 * configuration is authored once and applied to whichever version
 * arrives. The Enum is spelled out rather than computed so Orval
 * ships concrete LOINC codes to the frontend, and so a change to the
 * IG manifest surfaces as a failing drift test rather than silently
 * relaxing every jurisdiction's configuration. A unit test guards
 * that this enum stays in sync with the specification.
 */
export type TriggerCodeSection = typeof TriggerCodeSection[keyof typeof TriggerCodeSection];


export const TriggerCodeSection = {
  '10160-0': '10160-0',
  '11369-6': '11369-6',
  '11450-4': '11450-4',
  '18776-5': '18776-5',
  '29549-3': '29549-3',
  '30954-2': '30954-2',
  '42346-7': '42346-7',
  '46240-8': '46240-8',
  '47519-4': '47519-4',
} as const;
