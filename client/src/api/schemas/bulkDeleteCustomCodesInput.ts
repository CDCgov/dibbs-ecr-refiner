
/**
 * Input model for a bulk custom codes deletion request.
 */
export interface BulkDeleteCustomCodesInput {
  ids: string[];
  ids_to_skip: string[];
  delete_all: boolean;
}
