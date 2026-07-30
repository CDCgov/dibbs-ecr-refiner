import { DbConfigurationSectionProcessing } from '../../../../api/schemas/dbConfigurationSectionProcessing';
import { useToast } from '../../../../hooks/useToast';
import { useApiErrorFormatter } from '../../../../hooks/useErrorFormatter';
import {
  getGetConfigurationQueryKey,
  useUpdateSection,
} from '../../../../api/configurations/configurations';
import { useQueryClient } from '@tanstack/react-query';

export type SectionPatch = Partial<
  Pick<
    DbConfigurationSectionProcessing,
    'action' | 'include' | 'narrative' | 'code'
  >
>;

export function useSectionUpdater(configurationId: string) {
  const { mutate: updateSection } = useUpdateSection();
  const queryClient = useQueryClient();
  const formatError = useApiErrorFormatter();
  const showToast = useToast();

  return (
    currentSection: DbConfigurationSectionProcessing,
    patch: SectionPatch
  ) => {
    updateSection(
      {
        configurationId,
        data: {
          action: patch.action ?? currentSection.action,
          current_code: patch.code ?? currentSection.code,
          include: patch.include ?? currentSection.include,
          narrative: patch.narrative ?? currentSection.narrative,
        },
      },
      {
        onSuccess: async () => {
          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationId),
          });
        },
        onError: (error) => {
          const errorDetail =
            formatError(error) || error.message || 'Unknown error';
          showToast({
            heading: 'Section failed to update',
            body: errorDetail,
            variant: 'error',
          });
        },
      }
    );
  };
}
