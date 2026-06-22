
/**
 * These sections support the "reconstruct" narrative action.
 *
 * Currently, only Results is enabled; others are planned for future
 * iterations. Make sure to update unit tests to ensure only certain sections
 * are reconstructable.
 */
export type ReconstructableSection = typeof ReconstructableSection[keyof typeof ReconstructableSection];


export const ReconstructableSection = {
  '30954-2': '30954-2',
} as const;
