
export type ConfigurationCodeStatus = typeof ConfigurationCodeStatus[keyof typeof ConfigurationCodeStatus];


export const ConfigurationCodeStatus = {
  included: 'included',
  excluded: 'excluded',
} as const;
