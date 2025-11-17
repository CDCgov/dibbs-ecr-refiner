import { Icon } from '@trussworks/react-uswds';
import { useNavigate } from 'react-router';
import { useCreateConfiguration } from '../../api/configurations/configurations';
import { useApiErrorFormatter } from '../../hooks/useErrorFormatter';
import { useToast } from '../../hooks/useToast';
import { Button } from '../../components/Button';

interface DraftBannerProps {
  draftId: string | null;
  conditionId: string;
  step: 'build' | 'test' | 'activate';
}

export function DraftBanner({ draftId, conditionId, step }: DraftBannerProps) {
  const { mutate: createConfig } = useCreateConfiguration();
  const showToast = useToast();
  const navigate = useNavigate();
  const formatError = useApiErrorFormatter();

  const newDraftText =
    'Previous versions cannot be modified. You must draft a new version to make changes.';
  const editDraftText =
    'Previous versions cannot be modified. You can edit the existing draft.';
  return (
    <div className="bg-state-warning-lighter flex w-full flex-col gap-4 px-8 py-2 md:flex-row md:justify-between lg:px-20">
      <div className="flex items-center gap-2">
        <Icon.Info
          aria-hidden
          className="fill-state-warning-darker! shrink-0"
          size={3}
        />
        <p className="text-state-warning-darker font-bold">
          {draftId ? editDraftText : newDraftText}
        </p>
      </div>
      {draftId ? (
        <Button
          to={`/configurations/${draftId}/${step}`}
          className="self-start"
        >
          Go to draft
        </Button>
      ) : (
        <Button
          className="self-start"
          onClick={() =>
            createConfig(
              { data: { condition_id: conditionId } },
              {
                onSuccess: async (resp) => {
                  await navigate(`/configurations/${resp.data.id}/build`);
                  showToast({
                    heading: 'New configuration created',
                    body: resp.data.name ?? '',
                  });
                },
                onError: (e) => {
                  showToast({
                    heading: 'Configuration could not be created',
                    variant: 'error',
                    body: formatError(e),
                  });
                },
              }
            )
          }
        >
          Draft a new version
        </Button>
      )}
    </div>
  );
}
