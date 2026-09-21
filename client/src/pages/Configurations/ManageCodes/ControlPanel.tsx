import { Button } from '@components/Button';
import { Menu, MenuButton, MenuItem } from '@headlessui/react';
import { BaseMenuItems } from '@components/Dropdown';
import {
  CodeResponse,
  CodesLimitResponseValue,
  ConfigurationCodeStatusLabel,
} from '../../../api/schemas';
import { DeleteIcon } from './DeleteIcon';
import { useToast } from '../../../hooks/useToast';
import {
  getGetCodeCountsQueryKey,
  getGetCodeFiltersQueryKey,
  getGetCodesInfiniteQueryKey,
  useDeleteCustomCodes,
  useGetCodeCounts,
  useSetCodesStatus,
} from '../../../api/configurations/configurations';
import { useQueryClient } from '@tanstack/react-query';
import {
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@components/Modal';
import { useState } from 'react';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';
import { CodeFilters } from './Filters';
import { filterParamSerializer } from './Filters/utils';
import { Spinner } from '@components/Spinner';
import { useSelectedCodes } from './context/hook';

interface ControlPanelProps {
  renderedCodes: CodeResponse[];
  configurationId: string;
  filters: CodeFilters;
  hasNextPage: boolean;
}
export function ControlPanel({
  configurationId,
  filters,
  hasNextPage,
  renderedCodes,
}: ControlPanelProps) {
  const toast = useToast();
  const formatError = useApiErrorFormatter();
  const queryClient = useQueryClient();
  const { data: codeCounts } = useGetCodeCounts(configurationId);

  const { mutate: updateStatusWithinCursor } = useSetCodesStatus({
    axios: {
      paramsSerializer: filterParamSerializer,
    },
  });
  const [isOpen, setIsOpen] = useState(false);

  const { state, dispatch } = useSelectedCodes();
  const { selectedCodeIds, selectedCustomCodeIds, allSelected } = state;

  // These codes are unselected ones within the rendered cursor, or the anti-join
  // between the selected rows and the rendered ones, which we need in cases
  // where bulk selection is applied to "all but the selected" codes

  const deselectedCodesIds = renderedCodes
    .filter((c) => !c.is_custom)
    .map((c) => c.id)
    .filter((id) => !selectedCodeIds.has(id));

  const deselectedCustomCodesIds = renderedCodes
    .filter((c) => c.is_custom)
    .map((c) => c.id)
    .filter((id) => !selectedCodeIds.has(id));

  const updateSelectedCodesStatus = (status: ConfigurationCodeStatusLabel) => {
    updateStatusWithinCursor(
      {
        configurationId,
        params: {
          status: status === 'Included' ? 'included' : 'excluded',
          code_systems: filters.codeSystems.map((cs) => cs.id),
          sources: filters.sources.map((s) => s.id),
          statuses: filters.statuses.map((s) => s.id),
          search: filters.search,
          update_beyond_rendered_set: allSelected,
        },
        data: {
          code_ids: Array.from(selectedCodeIds),
          code_ids_to_skip: deselectedCodesIds,
        },
      },

      {
        onSuccess: async (resp) => {
          await queryClient.invalidateQueries({
            queryKey: getGetCodesInfiniteQueryKey(configurationId),
          });
          await queryClient.invalidateQueries({
            queryKey: getGetCodeCountsQueryKey(configurationId),
          });
          await queryClient.invalidateQueries({
            queryKey: getGetCodeFiltersQueryKey(configurationId),
          });
          toast({
            heading: `Code ${status}`,
            body: `${resp.data.length} codes ${status.toLowerCase()}`,
          });
          dispatch({
            type: 'reset',
          });
        },
        onError: (e) => {
          toast({
            heading: 'Codes could not be updated',
            body: formatError(e),
            variant: 'error',
          });
        },
      }
    );
  };

  const selectedCount = formatSelectedCodeCount(
    allSelected,
    filters,
    selectedCodeIds.size + selectedCustomCodeIds.size,
    deselectedCodesIds.length,
    deselectedCustomCodesIds.length,
    renderedCodes.length,
    hasNextPage,
    codeCounts?.data.primary_condition_rctc_count,
    codeCounts?.data.total_code_count
  );
  return (
    <>
      {
        <ExclusionWarningModal
          isOpen={isOpen}
          configurationId={configurationId}
          onClose={() => setIsOpen(false)}
          updateCodesToExcluded={() => updateSelectedCodesStatus('Excluded')}
          hasNextPage={hasNextPage}
          renderedCodes={renderedCodes}
        />
      }
      <div
        data-testid="control-panel"
        className="fixed bottom-5 left-1/2 -translate-x-1/2 rounded-xl bg-white px-6 py-4 shadow"
      >
        <div className="flex flex-row items-center justify-center gap-4">
          <span className="font-bold whitespace-nowrap">
            {selectedCount} selected
          </span>
          <div aria-hidden className="h-8 border border-gray-400!" />
          <div className="flex flex-row gap-6">
            <Button
              variant="unstyled"
              className="text-blue-cool-50 hover:bg-blue-cool-5 rounded border-2! px-4.5 py-2 text-sm! font-bold hover:cursor-pointer"
              onClick={() => updateSelectedCodesStatus('Included')}
            >
              Include
            </Button>
            <Button
              variant="unstyled"
              className="text-gray-cool-90 hover:bg-gray-5 rounded border-2! px-4.5 py-2 text-sm! font-bold hover:cursor-pointer"
              onClick={() => {
                if (selectedCustomCodeIds.size === 0) {
                  updateSelectedCodesStatus('Excluded');
                } else {
                  setIsOpen(true);
                }
              }}
            >
              Exclude
            </Button>
            {selectedCustomCodeIds.size > 0 ? (
              <CustomCodeDeletionMenu
                configurationId={configurationId}
                hasNextPage={hasNextPage}
                deselectedCustomCodeIds={deselectedCustomCodesIds}
              />
            ) : null}
          </div>
        </div>
      </div>
    </>
  );
}

interface CustomCodeDeletionMenuProps {
  configurationId: string;
  deselectedCustomCodeIds: string[];
  hasNextPage: boolean;
}

function CustomCodeDeletionMenu({
  configurationId,
  hasNextPage,
  deselectedCustomCodeIds,
}: CustomCodeDeletionMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { data: codeCounts } = useGetCodeCounts(configurationId);

  const { state } = useSelectedCodes();
  const { selectedCustomCodeIds, allSelected } = state;

  let totalCustomCodes = selectedCustomCodeIds.size;
  if (allSelected && codeCounts?.data.total_custom_codes_count) {
    totalCustomCodes = codeCounts.data.total_custom_codes_count;
  }

  const deletePastCursor = allSelected && hasNextPage;

  const customCodesToDeleteCount = deletePastCursor
    ? totalCustomCodes - deselectedCustomCodeIds.length
    : selectedCustomCodeIds.size;

  return (
    <>
      <CustomCodeDeletionModal
        configurationId={configurationId}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        totalCustomCodes={totalCustomCodes}
        deselectedCustomCodeIds={deselectedCustomCodeIds}
        deletePastCursor={deletePastCursor}
        customCodesToDeleteCount={customCodesToDeleteCount}
      />
      <Menu as="div" className="relative">
        <MenuButton
          as={Button}
          aria-label="More options"
          variant="unstyled"
          className="text-gray-cool-90 hover:bg-gray-5 rounded border-2! px-4 py-2 text-sm! font-bold hover:cursor-pointer"
        >
          ...
        </MenuButton>
        <BaseMenuItems
          portal
          anchor="top end"
          className="z-100 rounded bg-white shadow-lg ring-1 ring-black/5 focus:outline-none"
        >
          <MenuItem>
            <Button
              variant="unstyled"
              className="data-focus:bg-state-error-lighter text-state-error-dark flex flex-row items-center p-3 text-left text-sm! font-bold whitespace-nowrap data-focus:cursor-pointer"
              onClick={() => setIsOpen(true)}
            >
              <DeleteIcon />
              Delete {customCodesToDeleteCount} custom codes
            </Button>
          </MenuItem>
        </BaseMenuItems>
      </Menu>
    </>
  );
}

interface CustomCodeDeletionModalProps {
  isOpen: boolean;
  onClose: () => void;
  configurationId: string;
  totalCustomCodes: number;
  deselectedCustomCodeIds: string[];
  deletePastCursor: boolean;
  customCodesToDeleteCount: number;
}

function CustomCodeDeletionModal({
  isOpen,
  onClose,
  configurationId,
  deletePastCursor,
  deselectedCustomCodeIds,
  customCodesToDeleteCount,
}: CustomCodeDeletionModalProps) {
  const queryClient = useQueryClient();
  const { mutate } = useDeleteCustomCodes();
  const toast = useToast();

  const { state, dispatch } = useSelectedCodes();
  const { selectedCustomCodeIds } = state;

  const deleteCustomCodes = () => {
    mutate(
      {
        configurationId,
        data: {
          ids: Array.from(selectedCustomCodeIds),
          ids_to_skip: deselectedCustomCodeIds,
          delete_all: deletePastCursor,
        },
      },
      {
        onSuccess: async (resp) => {
          await queryClient.invalidateQueries({
            queryKey: getGetCodesInfiniteQueryKey(configurationId),
          });
          await queryClient.invalidateQueries({
            queryKey: getGetCodeCountsQueryKey(configurationId),
          });
          await queryClient.invalidateQueries({
            queryKey: getGetCodeFiltersQueryKey(configurationId),
          });
          toast({
            heading: 'Codes updated',
            body: `${resp.data.length} custom codes deleted.`,
          });
          dispatch({
            type: 'reset',
          });
        },
        onError: () => {
          toast({
            heading: 'Codes could not be updated',
            body: 'Deleting custom codes was unsuccessful. Please try again.',
            variant: 'error',
          });
        },
      }
    );
  };

  return (
    <Modal open={isOpen} onClose={onClose} position="center">
      <ModalHeader>
        <ModalTitle>
          {customCodesToDeleteCount} custom codes will be deleted
        </ModalTitle>
      </ModalHeader>
      <ModalBody>
        <p>
          Custom codes can only be deleted from a configuration. Codes found
          within TES code sets will be excluded, not deleted.
        </p>
      </ModalBody>
      <ModalFooter align="left">
        <div className="flex flex-row items-center gap-6">
          <Button
            variant="unstyled"
            className="bg-state-error-dark rounded p-4 font-bold text-white hover:cursor-pointer hover:bg-[#8b0a03]"
            onClick={() => {
              deleteCustomCodes();
              onClose();
            }}
          >
            Delete {customCodesToDeleteCount} codes
          </Button>
          <Button
            variant="unstyled"
            className="text-violet-warm-60 font-bold hover:cursor-pointer"
            onClick={onClose}
          >
            Cancel
          </Button>
        </div>
      </ModalFooter>
    </Modal>
  );
}

interface CountResult {
  totalCodeCount: number;
  totalCustomCodeCount: number;
  excludeableCodeCount: number;
  exclusionForbidden: boolean;
}

function calculateCounts(
  allSelected: boolean,
  selectedCodeIds: Set<string>,
  selectedCustomCodeIds: Set<string>,
  renderedCodes: CodeResponse[],
  total_code_count: number,
  total_custom_codes_count: number,
  lockedCodesCount: number,
  hasNextPage: boolean
): CountResult {
  if (allSelected && hasNextPage) {
    // If in the all selected case, start with the totals as fetched from the
    // code counts hook and tally any custom codes we've selected. Forbid exclusion
    // only if we've down-selected to a subset with only custom codes
    const deselectedCodeCount = renderedCodes.filter(
      (c) => !selectedCodeIds.has(c.id)
    ).length;

    const totalCodeCount = total_code_count;
    const totalCustomCodeCount = total_custom_codes_count;

    const excludeableCodeCount =
      totalCodeCount -
      deselectedCodeCount -
      totalCustomCodeCount -
      lockedCodesCount;

    return {
      totalCodeCount,
      totalCustomCodeCount,
      excludeableCodeCount,
      exclusionForbidden: excludeableCodeCount <= 0,
    };
  }

  // If in the progressive section case, start with the number of selected codes
  // and forbid exclusion if they're all custom codes.
  const totalCodeCount = selectedCodeIds.size + selectedCustomCodeIds.size;
  const totalCustomCodeCount = selectedCustomCodeIds.size;
  const excludeableCodeCount = totalCodeCount - totalCustomCodeCount;

  return {
    totalCodeCount,
    totalCustomCodeCount,
    excludeableCodeCount,
    exclusionForbidden: excludeableCodeCount === 0,
  };
}

interface ExclusionWarningModalProps {
  configurationId: string;
  isOpen: boolean;
  onClose: () => void;
  updateCodesToExcluded: () => void;
  renderedCodes: CodeResponse[];
  hasNextPage: boolean;
}

function ExclusionWarningModal({
  configurationId,
  isOpen,
  onClose,
  updateCodesToExcluded,
  hasNextPage,
  renderedCodes,
}: ExclusionWarningModalProps) {
  const {
    data: codeCounts,
    isPending,
    isError,
  } = useGetCodeCounts(configurationId);

  const { state } = useSelectedCodes();
  const { selectedCodeIds, selectedCustomCodeIds, allSelected } = state;

  if (isPending) return <Spinner variant="centered" />;
  if (isError) return 'Error!';

  const {
    totalCodeCount,
    totalCustomCodeCount,
    excludeableCodeCount,
    exclusionForbidden,
  } = calculateCounts(
    allSelected,
    selectedCodeIds,
    selectedCustomCodeIds,
    renderedCodes,
    codeCounts?.data.total_code_count,
    codeCounts?.data.total_custom_codes_count,
    codeCounts.data.primary_condition_rctc_count,
    hasNextPage
  );
  const lockedCodesCount = codeCounts.data.primary_condition_rctc_count;
  return (
    <Modal open={isOpen} onClose={onClose} position="center">
      <ModalHeader>
        <ModalTitle>Exclude codes</ModalTitle>
      </ModalHeader>
      <ModalBody>
        <div className="flex flex-col gap-4">
          <p>
            {exclusionForbidden
              ? 'None of the selected codes can be excluded.'
              : `
            ${excludeableCodeCount} of ${totalCodeCount} selected codes will be
            excluded from this configuration.`}
          </p>
          <p className="flex flex-col border-l-3! border-l-[#d54309] bg-[#fdf3f2] px-4 py-3">
            <span>
              {totalCustomCodeCount} custom code(s) can't be excluded. Custom
              codes can only be deleted to remove them from this configuration.
            </span>

            <span className="mt-2">
              {lockedCodesCount
                ? `This configuration's primary condition has ${lockedCodesCount} RCTC code(s) that can't be excluded. These codes must be included to properly process the eCR.`
                : null}
            </span>
          </p>
        </div>
      </ModalBody>
      <ModalFooter align="left">
        <div className="flex flex-row items-center gap-6">
          {exclusionForbidden ? null : (
            <Button
              onClick={() => {
                updateCodesToExcluded();
                onClose();
              }}
            >
              Exclude {excludeableCodeCount} codes
            </Button>
          )}
          <Button
            variant="unstyled"
            className="text-violet-warm-60 font-bold hover:cursor-pointer"
            onClick={onClose}
          >
            Cancel
          </Button>
        </div>
      </ModalFooter>
    </Modal>
  );
}
function formatSelectedCodeCount(
  allSelected: boolean,
  filters: CodeFilters,
  selectedCodeCount: number,
  deselectedCodesCount: number,
  deselectedCustomCodesCount: number,
  renderedCodeCount: number,
  hasNextPage: boolean,
  lockedCodesCount?: number,
  totalCodeCount?: number
): string {
  // If the rendered code count is under the pagination limit, or we're not in the bulk selection case
  // just return the selected values
  if (renderedCodeCount < CodesLimitResponseValue.codes_limit || !allSelected) {
    return selectedCodeCount.toString();
  }

  // Otherwise, check the active filters and tabulate the values
  const hasFilterEntry = (arr?: { count?: number }[]) => arr && arr.length > 0;

  const atLeastOneFilterActive =
    hasFilterEntry(filters.codeSystems) ||
    hasFilterEntry(filters.sources) ||
    hasFilterEntry(filters.statuses) ||
    filters.search;

  if (!atLeastOneFilterActive) {
    return totalCodeCount
      ? (
          totalCodeCount -
          deselectedCodesCount -
          deselectedCustomCodesCount -
          (lockedCodesCount ?? 0)
        ).toString()
      : 'All ';
  }

  return selectedCodeCount > CodesLimitResponseValue.codes_limit || hasNextPage
    ? `${CodesLimitResponseValue.codes_limit}+ codes`
    : selectedCodeCount.toString();
}
