import { useNavigate } from 'react-router';
import { useCreateConfiguration } from '../../../api/configurations/configurations';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';
import { useToast } from '../../../hooks/useToast';
import { Button } from '@components/Button';
import { useState } from 'react';
import {
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@components/Modal';
import { InfoIcon } from '@components/Icons/InfoIcon';
import { LayoutContainer } from '@components/Layout/LayoutContainer';
import { useGetStep } from './useGetStep';

interface DraftBannerProps {
  draftId: string | null;
  conditionId: string;
  latestVersion: number;
}

export function DraftBanner({
  draftId,
  conditionId,
  latestVersion,
}: DraftBannerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const step = useGetStep();

  const newDraftText =
    'Previous versions cannot be modified. You must draft a new version to make changes.';
  const editDraftText =
    'Previous versions cannot be modified. You can edit the existing draft.';
  return (
    <LayoutContainer
      breakout
      background="bg-yellow-vivid-5v border-b-3 border-yellow-vivid-30v"
      padding="none"
      className="z-banner-interactive px-8 py-4 lg:px-20"
      maxWidth="max-w-7xl"
    >
      <div className="w-full">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <InfoIcon className="fill-violet-warm-70 shrink-0" />
            <p className="text-violet-warm-70 font-bold">
              {draftId ? editDraftText : newDraftText}
            </p>
          </div>
          {draftId ? (
            <Button
              to={`/configurations/${draftId}/${step}`}
              className="bg-violet-warm-60 self-start text-white"
            >
              Go to draft
            </Button>
          ) : (
            <Button
              onClick={() => setIsOpen(true)}
              className="bg-violet-warm-60 text-white"
            >
              Draft a new version
            </Button>
          )}
          <NewDraftModal
            isOpen={isOpen}
            onClose={() => setIsOpen(false)}
            conditionId={conditionId}
            version={latestVersion}
          />
        </div>
      </div>
    </LayoutContainer>
  );
}

interface NewDraftModalProps {
  isOpen: boolean;
  onClose: () => void;
  conditionId: string;
  version: number;
}
function NewDraftModal({
  isOpen,
  onClose,
  conditionId,
  version,
}: NewDraftModalProps) {
  const { mutate: createConfig } = useCreateConfiguration();
  const showToast = useToast();
  const navigate = useNavigate();
  const formatError = useApiErrorFormatter();

  const newVersion = version + 1;

  return (
    <Modal open={isOpen} onClose={onClose} position="top">
      <ModalHeader>
        <ModalTitle>Draft a new version?</ModalTitle>
      </ModalHeader>
      <ModalBody>
        <p className="max-w-100">
          Are you sure you want to draft a new version? This will clone the
          latest version (Version {version}) as the basis for a new draft
          version (Version {newVersion}).
        </p>
      </ModalBody>
      <ModalFooter align="right">
        <Button
          onClick={() =>
            createConfig(
              { data: { condition_id: conditionId } },
              {
                onSuccess: async (resp) => {
                  await navigate(
                    `/configurations/${resp.data.id}/customize-sections`
                  );
                  showToast({
                    heading: 'New draft created',
                    body: `Version ${newVersion}`,
                  });
                },
                onError: (e) => {
                  showToast({
                    heading: 'Draft could not be created',
                    variant: 'error',
                    body: formatError(e),
                  });
                },
              }
            )
          }
        >
          Yes, draft a new version
        </Button>
      </ModalFooter>
    </Modal>
  );
}
