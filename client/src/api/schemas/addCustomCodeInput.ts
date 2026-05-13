import type { CodeSystem } from './codeSystem';

/**
 * Input model for adding a custom code to a configuration.
 */
export interface AddCustomCodeInput {
  code: string;
  system: CodeSystem;
  name: string;
}
