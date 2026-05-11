import type { ValidationError } from './validationError';

export interface HTTPValidationError {
  detail?: ValidationError[];
}
