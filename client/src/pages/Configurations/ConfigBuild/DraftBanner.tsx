import {
  Icon,
  Modal,
  ModalFooter,
  ModalHeading,
  ModalRef,
} from '@trussworks/react-uswds';
import { useNavigate } from 'react-router';
import { useCreateConfiguration } from '../../../api/configurations/configurations';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';
import { useToast } from '../../../hooks/useToast';
import { Button } from '../../../components/Button';
import { useRef } from 'react';
import classNames from 'classnames';
import { ModalToggleButton } from '../../../components/Button/ModalToggleButton';

interface DraftBannerProps {
  draftId: string | null;
  conditionId: string;
  latestVersion: number;
  step: 'build' | 'test' | 'activate';
}

export function DraftBanner({
  draftId,
  conditionId,
  latestVersion,
  step,
}: DraftBannerProps) {
  const modalRef = useRef<ModalRef>(null);

  const newDraftText =
    'Previous versions cannot be modified. You must draft a new version to make changes.';
  const editDraftText =
    'Previous versions cannot be modified. You can edit the existing draft.';
  return (
    <div className="bg-state-warning-lighter flex w-full flex-col gap-4 px-8 py-2 shadow-lg md:flex-row md:justify-between lg:px-20">
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
        <ModalToggleButton
          modalRef={modalRef}
          opener
          className={classNames('self-start')}
        >
          Draft a new version
        </ModalToggleButton>
      )}
      <NewDraftModal
        modalRef={modalRef}
        conditionId={conditionId}
        version={latestVersion}
      />
    </div>
  );
}

interface NewDraftModalProps {
  modalRef: React.Ref<ModalRef | null>;
  conditionId: string;
  version: number;
}
function NewDraftModal({ modalRef, conditionId, version }: NewDraftModalProps) {
  const { mutate: createConfig } = useCreateConfiguration();
  const showToast = useToast();
  const navigate = useNavigate();
  const formatError = useApiErrorFormatter();

  const newVersion = version + 1;

  return (
    <Modal
      id="draft-modal"
      className="align-top!"
      ref={modalRef}
      aria-labelledby="draft-modal-heading"
      aria-describedby="draft-modal-text"
    >
      <ModalHeading id="draft-modal-heading">Draft a new version?</ModalHeading>
      <p id="draft-modal-text" className="my-6">
        Are you sure you want to draft a new version? This will clone the latest
        version (Version {version}) as the basis for a new draft version
        (Version {newVersion}).
      </p>
      <ModalFooter className="flex justify-end">
        <Button
          onClick={() =>
            createConfig(
              { data: { condition_id: conditionId } },
              {
                onSuccess: async (resp) => {
                  await navigate(`/configurations/${resp.data.id}/build`);
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
