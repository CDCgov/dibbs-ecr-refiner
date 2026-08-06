
/**
 * Body required to generate a TES update diff for a specific condition.
 */
export interface ExportDiffInput {
  cond_canonical_url: string;
  cur_tes_version: string;
  prev_tes_version: string;
}
