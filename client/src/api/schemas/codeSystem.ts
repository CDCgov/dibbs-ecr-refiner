
/**
 * An Enum for code systems.
 */
export type CodeSystem = typeof CodeSystem[keyof typeof CodeSystem];


export const CodeSystem = {
  LOINC: 'LOINC',
  SNOMED: 'SNOMED',
  'ICD-10': 'ICD-10',
  RxNorm: 'RxNorm',
  CVX: 'CVX',
  Other: 'Other',
} as const;
