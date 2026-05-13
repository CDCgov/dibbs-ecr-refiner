import type { CodeSystem } from './codeSystem';

/**
 * Custom code associated with a Configuration.
 */
export interface DbConfigurationCustomCode {
  code: string;
  system: CodeSystem;
  name: string;
}
