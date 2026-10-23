
/**
 * A code and the label to render for it, with **no code system**.
 *
 * Safe only where the surrounding structure establishes the system -- a condition's
 * RSG codes are SNOMED by construction, for instance. It is deliberately _not_
 * enough to match on: a code without a system is not resolvable, and the name is
 * chosen to read wrong in matching code. Use `Coding` there.
 */
export interface CodeLabel {
  code: string;
  display_name: string;
}
