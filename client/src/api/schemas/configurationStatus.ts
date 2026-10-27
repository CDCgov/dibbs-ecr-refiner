
export type ConfigurationStatus = typeof ConfigurationStatus[keyof typeof ConfigurationStatus];


export const ConfigurationStatus = {
  draft: 'draft',
  inactive: 'inactive',
  active: 'active',
} as const;
