export enum CodeSystem {
  LOINC = 'loinc',
  SNOMED = 'snomed',
  RxNorm = 'rxnorm',
  Other = 'other',
}

export type SupportedCodeSystems = CodeSystem;

export function normalizeSystem(value: string) {
  return value;
}
