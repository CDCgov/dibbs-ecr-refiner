
/**
 * Body required to generate a TES update diff for a specific condition.
 */
export interface ExportDiffInput {
  cond_canonical_url: string;
  new_tes_version: string;
  old_tes_version: string;
}
