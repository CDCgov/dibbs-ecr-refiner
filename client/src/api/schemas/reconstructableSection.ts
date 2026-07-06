
/**
 * These sections support the "reconstruct" narrative action.
 *
 * Results, Problems, Immunizations, and Medications Administered are
 * enabled. Make sure to update unit tests to ensure only certain sections
 * are reconstructable.
 */
export type ReconstructableSection = typeof ReconstructableSection[keyof typeof ReconstructableSection];


export const ReconstructableSection = {
  '30954-2': '30954-2',
  '11450-4': '11450-4',
  '11369-6': '11369-6',
  '29549-3': '29549-3',
} as const;
