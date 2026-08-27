import { Button } from '@components/Button';
import {
  getGetCodeCountsQueryKey,
  getGetCodeFiltersQueryKey,
  getGetCodesInfiniteQueryKey,
  getGetConfigurationQueryKey,
  useDeleteCustomCodeFromConfiguration,
} from '../../../../api/configurations/configurations';
import { useQueryClient } from '@tanstack/react-query';
import { useToast } from '../../../../hooks/useToast';

interface DeleteCustomCodeButtonProps {
  configurationId: string;
  id: string;
  code: string;
}

export function DeleteCustomCodeButton({
  configurationId,
  id,
  code,
}: DeleteCustomCodeButtonProps) {
  const queryClient = useQueryClient();
  const showToast = useToast();
  const { mutate } = useDeleteCustomCodeFromConfiguration();

  const handleDelete = () => {
    mutate(
      { configurationId, id },
      {
        onSuccess: async () => {
          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationId),
          });
          await queryClient.invalidateQueries({
            queryKey: getGetCodesInfiniteQueryKey(configurationId),
          });
          await queryClient.invalidateQueries({
            queryKey: getGetCodeCountsQueryKey(configurationId),
          });
          await queryClient.invalidateQueries({
            queryKey: getGetCodeFiltersQueryKey(configurationId),
          });
          showToast({
            heading: 'Deleted code',
            body: code,
          });
        },
      }
    );
  };
  return (
    <Button
      className="text-state-error-dark text-sm! font-semibold hover:cursor-pointer hover:underline"
      variant="unstyled"
      onClick={handleDelete}
      aria-label="Delete custom code"
    >
      Delete
    </Button>
  );
}
