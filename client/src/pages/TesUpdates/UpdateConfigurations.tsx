import { Dialog, DialogPanel, DialogTitle } from '@headlessui/react';
import { Button } from '@components/Button';
import { Checkbox } from '@components/Checkbox';
import { Spinner } from '@components/Spinner';
import { Table } from '@components/Table';
import { Title } from '@components/Title';
import { useNavigate } from 'react-router';
import { useState } from 'react';
import {
  useApplyTesUpdatesToExistingDrafts,
  // useCreateDraftsFromActiveConfigurations,
  useGetConfigurationsToUpdate,
} from '../../api/tes/tes';
import { useToast } from '../../hooks/useToast';

export function UpdateConfigurations() {
  const navigate = useNavigate();
  const showToast = useToast();

  const {
    data: response,
    isPending,
    isError,
    refetch,
  } = useGetConfigurationsToUpdate();

  const applyExistingDraftUpdates = useApplyTesUpdatesToExistingDrafts();

  /*
   * VERIFY WITH THE PARALLEL STORY:
   * Change this hook if their generated hook uses a different name.
   */
  // const createDraftsFromActiveConfigurations =
  //   useCreateDraftsFromActiveConfigurations();

  const [selectedConfigurations, setSelectedConfigurations] = useState<
    string[]
  >([]);

  const [confirmationModalOpen, setConfirmationModalOpen] = useState(false);

  const [submissionError, setSubmissionError] = useState<string | null>(null);

  if (isPending) {
    return <Spinner variant="centered" />;
  }

  if (isError) {
    return 'Error!';
  }

  const existingDrafts = response.data.existing_drafts;
  const draftsToCreate = response.data.drafts_to_create;

  const existingDraftIds = existingDrafts.map(
    (draft) => draft.configuration_id
  );

  const activeConfigurationIds = draftsToCreate.map(
    (configuration) => configuration.configuration_id
  );

  const selectedExistingDraftIds = existingDraftIds.filter((id) =>
    selectedConfigurations.includes(id)
  );

  const selectedActiveConfigurationIds = activeConfigurationIds.filter((id) =>
    selectedConfigurations.includes(id)
  );

  // const isSubmitting =
  //   applyExistingDraftUpdates.isPending ||
  //   createDraftsFromActiveConfigurations.isPending;

  const isSubmitting = applyExistingDraftUpdates.isPending;

  function handleIndividualSelection(configurationId: string) {
    setSelectedConfigurations((currentSelection) => {
      if (currentSelection.includes(configurationId)) {
        return currentSelection.filter((id) => id !== configurationId);
      }

      return [...currentSelection, configurationId];
    });
  }

  function areAllSelected(configurationIds: string[]) {
    return (
      configurationIds.length > 0 &&
      configurationIds.every((id) => selectedConfigurations.includes(id))
    );
  }

  function areSomeSelected(configurationIds: string[]) {
    return (
      !areAllSelected(configurationIds) &&
      configurationIds.some((id) => selectedConfigurations.includes(id))
    );
  }

  function handleBulkSelection(configurationIds: string[]) {
    setSelectedConfigurations((currentSelection) => {
      const allSelected =
        configurationIds.length > 0 &&
        configurationIds.every((id) => currentSelection.includes(id));

      if (allSelected) {
        return currentSelection.filter((id) => !configurationIds.includes(id));
      }

      return [...new Set([...currentSelection, ...configurationIds])];
    });
  }

  function openConfirmationModal() {
    if (selectedConfigurations.length === 0) {
      return;
    }

    setSubmissionError(null);
    setConfirmationModalOpen(true);
  }

  function closeConfirmationModal() {
    if (isSubmitting) {
      return;
    }

    setSubmissionError(null);
    setConfirmationModalOpen(false);
  }

  async function updateSelectedExistingDrafts() {
    if (selectedExistingDraftIds.length === 0) {
      return 0;
    }

    const mutationResponse = await applyExistingDraftUpdates.mutateAsync({
      data: {
        configuration_ids: selectedExistingDraftIds,
      },
    });

    return mutationResponse.data.updated_count;
  }

  // async function createSelectedDrafts() {
  //   if (selectedActiveConfigurationIds.length === 0) {
  //     return 0;
  //   }
  //
  //   /*
  //    * VERIFY WITH THE PARALLEL STORY:
  //    *
  //    * This assumes the request uses configuration_ids and the response
  //    * uses created_count.
  //    */
  //   const mutationResponse =
  //     await createDraftsFromActiveConfigurations.mutateAsync({
  //       data: {
  //         configuration_ids: selectedActiveConfigurationIds,
  //       },
  //     });
  //
  //   return mutationResponse.data.created_count;
  // }

  async function handleConfirmUpdates() {
    setSubmissionError(null);

    try {
      const updatedCount = await updateSelectedExistingDrafts();

      // const createdCount = await createSelectedDrafts();
      const createdCount = 0;

      const totalCount = updatedCount + createdCount;

      await refetch();

      setSelectedConfigurations([]);
      setConfirmationModalOpen(false);

      await navigate('/configurations');

      showToast({
        heading: 'Configurations have been updated',
        body:
          totalCount === 1
            ? '1 configuration was updated.'
            : `${totalCount} configurations were updated.`,
      });
    } catch {
      /*
       * One endpoint may have succeeded before the other failed.
       * Refetch so the page shows the actual database state.
       */
      await refetch();

      setSubmissionError(
        'We could not apply all of the selected TES updates. Please try again.'
      );
    }
  }

  return (
    <div>
      <Title className="py-4">Update configurations</Title>

      <h2 className="mb-1 text-[1.25rem] font-bold">
        Update to latest release
      </h2>

      <p className="max-w-[45rem]">
        Update existing drafts and/or create a for existing configurations to
        apply the latest TES release. Drafts will need to be activated in order
        to receive the most up to date eCRs.
      </p>

      <div className="mt-4 bg-white px-10 py-6 lg:max-w-[75%]">
        <Table className="mt-0 mb-4 border-none">
          <caption className="text-lg! font-bold">
            Update existing drafts
          </caption>

          <thead>
            <tr>
              <th scope="col" className="bg-white! pl-0! font-bold">
                <div className="flex items-center gap-2">
                  <Checkbox
                    onClick={() => handleBulkSelection(existingDraftIds)}
                    checked={areAllSelected(existingDraftIds)}
                    aria-checked={
                      areSomeSelected(existingDraftIds)
                        ? 'mixed'
                        : areAllSelected(existingDraftIds)
                    }
                    aria-label="Select all existing drafts"
                  />

                  <span>Configuration</span>
                </div>
              </th>

              <th scope="col" className="bg-white! pl-0! font-bold">
                Current TES version
              </th>

              <th scope="col" className="bg-white! pl-0! font-bold">
                Code sets to update
              </th>
            </tr>
          </thead>

          <tbody>
            {existingDrafts.length === 0 ? (
              <tr>
                <td className="pl-0!" colSpan={3}>
                  No existing drafts need to be updated.
                </td>
              </tr>
            ) : (
              existingDrafts.map((draft) => (
                <tr key={draft.configuration_id}>
                  <td className="pl-0!">
                    <div className="flex items-center gap-2">
                      <Checkbox
                        onClick={() =>
                          handleIndividualSelection(draft.configuration_id)
                        }
                        checked={selectedConfigurations.includes(
                          draft.configuration_id
                        )}
                        aria-label={`Select ${draft.configuration_name}`}
                      />

                      <span>{draft.configuration_name}</span>
                    </div>
                  </td>

                  <td className="pl-0!">{draft.configuration_tes_version}</td>

                  <td className="pl-0!">
                    {draft.codesets_to_update.join(', ')}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </Table>

        <Table className="mt-0 mb-4 border-none">
          <caption className="mb-0 text-lg! font-bold">
            Create draft to update
          </caption>

          <thead>
            <tr>
              <th scope="col" className="bg-white! pl-0! font-bold">
                <div className="flex items-center gap-2">
                  <Checkbox
                    onClick={() => handleBulkSelection(activeConfigurationIds)}
                    checked={areAllSelected(activeConfigurationIds)}
                    aria-checked={
                      areSomeSelected(activeConfigurationIds)
                        ? 'mixed'
                        : areAllSelected(activeConfigurationIds)
                    }
                    aria-label="Select all configurations requiring a draft"
                  />

                  <span>Configuration</span>
                </div>
              </th>

              <th scope="col" className="bg-white! pl-0! font-bold">
                Current TES version
              </th>

              <th scope="col" className="bg-white! pl-0! font-bold">
                Code sets to update
              </th>
            </tr>
          </thead>

          <tbody>
            {draftsToCreate.length === 0 ? (
              <tr>
                <td className="pl-0!" colSpan={3}>
                  No active configurations require a new draft.
                </td>
              </tr>
            ) : (
              draftsToCreate.map((configuration) => (
                <tr key={configuration.configuration_id}>
                  <td className="pl-0!">
                    <div className="flex items-center gap-2">
                      <Checkbox
                        onClick={() =>
                          handleIndividualSelection(
                            configuration.configuration_id
                          )
                        }
                        checked={selectedConfigurations.includes(
                          configuration.configuration_id
                        )}
                        aria-label={`Select ${configuration.configuration_name}`}
                      />

                      <span>{configuration.configuration_name}</span>
                    </div>
                  </td>

                  <td className="pl-0!">
                    {configuration.configuration_tes_version}
                  </td>

                  <td className="pl-0!">
                    {configuration.codesets_to_update.join(', ')}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </Table>

        <Button
          disabled={selectedConfigurations.length === 0}
          onClick={openConfirmationModal}
        >
          Apply updates
        </Button>
      </div>

      <UpdateConfirmationModal
        open={confirmationModalOpen}
        existingDraftCount={selectedExistingDraftIds.length}
        newDraftCount={selectedActiveConfigurationIds.length}
        isSubmitting={isSubmitting}
        errorMessage={submissionError}
        onCancel={closeConfirmationModal}
        onConfirm={handleConfirmUpdates}
      />
    </div>
  );
}

interface UpdateConfirmationModalProps {
  open: boolean;
  existingDraftCount: number;
  newDraftCount: number;
  isSubmitting: boolean;
  errorMessage: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}

function UpdateConfirmationModal({
  open,
  existingDraftCount,
  newDraftCount,
  isSubmitting,
  errorMessage,
  onCancel,
  onConfirm,
}: UpdateConfirmationModalProps) {
  const title = getConfirmationTitle(existingDraftCount, newDraftCount);

  const confirmButtonText = getConfirmationButtonText(
    existingDraftCount,
    newDraftCount,
    isSubmitting
  );

  return (
    <Dialog open={open} onClose={onCancel} className="relative z-50">
      <div className="fixed inset-0 bg-black/40" aria-hidden="true" />

      <div className="fixed inset-0 flex items-center justify-center p-4">
        <DialogPanel className="w-full max-w-lg bg-white p-8 shadow-lg">
          <div className="flex items-start justify-between gap-4">
            <DialogTitle className="text-3xl font-bold">{title}</DialogTitle>

            <Button
              className="text-gray-cool-60 cursor-pointer text-2xl leading-none"
              variant="unstyled"
              onClick={onCancel}
              disabled={isSubmitting}
              aria-label="Close confirmation modal"
            >
              ×
            </Button>
          </div>

          <ConfirmationDescription
            existingDraftCount={existingDraftCount}
            newDraftCount={newDraftCount}
          />

          <div className="border-blue-cool-40 bg-blue-cool-5 mt-5 border-l-4 px-4 py-3">
            <p className="font-bold">Note</p>

            <ConfirmationNote
              existingDraftCount={existingDraftCount}
              newDraftCount={newDraftCount}
            />
          </div>

          {errorMessage && (
            <div
              className="mt-4 border-l-4 border-red-600 bg-red-50 px-4 py-3 text-red-900"
              role="alert"
            >
              {errorMessage}
            </div>
          )}

          <div className="mt-6 flex gap-3">
            <Button onClick={onConfirm} disabled={isSubmitting}>
              {confirmButtonText}
            </Button>

            <Button
              variant="tertiary"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
          </div>
        </DialogPanel>
      </div>
    </Dialog>
  );
}

interface ConfirmationCounts {
  existingDraftCount: number;
  newDraftCount: number;
}

function ConfirmationDescription({
  existingDraftCount,
  newDraftCount,
}: ConfirmationCounts) {
  if (existingDraftCount > 0 && newDraftCount > 0) {
    return (
      <div className="mt-4 space-y-2">
        <p>
          {formatCount(existingDraftCount, 'existing draft', 'existing drafts')}{' '}
          will be updated to use the latest TES release.
        </p>

        <p>
          {formatCount(newDraftCount, 'new draft', 'new drafts')} will be
          created from the selected active configurations.
        </p>
      </div>
    );
  }

  if (existingDraftCount > 0) {
    return (
      <p className="mt-4">
        {formatCount(existingDraftCount, 'draft', 'drafts')} will be updated to
        use the latest TES release.
      </p>
    );
  }

  return (
    <p className="mt-4">
      {formatCount(newDraftCount, 'new draft', 'new drafts')} will be created
      using the latest TES release.
    </p>
  );
}

function ConfirmationNote({
  existingDraftCount,
  newDraftCount,
}: ConfirmationCounts) {
  if (existingDraftCount > 0 && newDraftCount > 0) {
    return (
      <p>
        Existing drafts will be changed, but the selected active configurations
        will not be changed. All new and updated drafts must still be activated
        before their TES changes are used to refine eCRs.
      </p>
    );
  }

  if (existingDraftCount > 0) {
    return (
      <p>
        This changes the selected drafts. They must still be activated before
        the updated code sets are used to refine eCRs.
      </p>
    );
  }

  return (
    <p>
      The selected active configurations will not be changed. The new drafts
      must be activated before their updated code sets are used to refine eCRs.
    </p>
  );
}

function getConfirmationTitle(
  existingDraftCount: number,
  newDraftCount: number
) {
  if (existingDraftCount > 0 && newDraftCount > 0) {
    return 'Apply TES updates?';
  }

  if (existingDraftCount > 0) {
    return existingDraftCount === 1 ? 'Update draft?' : 'Update drafts?';
  }

  return newDraftCount === 1 ? 'Create draft?' : 'Create drafts?';
}

function getConfirmationButtonText(
  existingDraftCount: number,
  newDraftCount: number,
  isSubmitting: boolean
) {
  if (isSubmitting) {
    return 'Applying updates…';
  }

  if (existingDraftCount > 0 && newDraftCount > 0) {
    return 'Yes, apply updates';
  }

  if (existingDraftCount > 0) {
    return existingDraftCount === 1
      ? 'Yes, update draft'
      : 'Yes, update drafts';
  }

  return newDraftCount === 1 ? 'Yes, create draft' : 'Yes, create drafts';
}

function formatCount(
  count: number,
  singularLabel: string,
  pluralLabel: string
) {
  return `${count} ${count === 1 ? singularLabel : pluralLabel}`;
}
