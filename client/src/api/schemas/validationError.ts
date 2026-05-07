import type { ValidationErrorCtx } from './validationErrorCtx';

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
  input?: unknown;
  ctx?: ValidationErrorCtx;
}
