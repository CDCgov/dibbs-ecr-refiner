
/**
 * Utility class to help Orval ship these values to the frontend.
 */
export const CodesLimitResponseValue = {
  codes_limit: 100,
} as const;
export type CodesLimitResponse = typeof CodesLimitResponseValue;
