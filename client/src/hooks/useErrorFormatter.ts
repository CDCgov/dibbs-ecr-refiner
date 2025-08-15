import axios from 'axios';
import { HTTPValidationError } from '../api/schemas';

export function useApiErrorFormatter() {
  return (error: unknown) => {
    if (axios.isAxiosError<HTTPValidationError>(error)) {
      const detail = error.response?.data?.detail;
      const detailMsg = formatDetail(detail);
      if (detailMsg) return detailMsg;

      if (typeof error.message === 'string' && error.message.trim()) {
        return error.message;
      }
    }
    return 'An unexpected error occurred. Please try again.';
  };
}

function formatDetail(detail: unknown): string {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.join(', ');
  if (detail && typeof detail === 'object') {
    try {
      return JSON.stringify(detail);
    } catch {
      return 'An unexpected error occurred.';
    }
  }
  return '';
}
