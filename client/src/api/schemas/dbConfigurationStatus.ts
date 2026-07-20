
export type DbConfigurationStatus = typeof DbConfigurationStatus[keyof typeof DbConfigurationStatus];


export const DbConfigurationStatus = {
  draft: 'draft',
  inactive: 'inactive',
  active: 'active',
} as const;
