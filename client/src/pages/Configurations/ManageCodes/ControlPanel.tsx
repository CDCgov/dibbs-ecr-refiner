import { Button } from '@components/Button';
import { Menu, MenuButton, MenuItem } from '@headlessui/react';
import { BaseMenuItems } from '@components/Dropdown';
import {
  CodeResponse,
  CodeResponseStatus,
  CodesLimitResponseValue,
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

interface ControlPanelProps {
  configurationId: string;
  selectedCodeIds: Set<string>;
  selectedCustomCodes: CodeResponse[];
  clearSelections: () => void;
  allSelected: boolean;
  renderedCodes: CodeResponse[];
  filters: CodeFilters;
}
export function ControlPanel({
  configurationId,
  selectedCodeIds,
  selectedCustomCodes,
  clearSelections,
  allSelected,
  renderedCodes,
  filters,
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

  // These custom codes can be deleted
  const customCodeIds = new Set(selectedCustomCodes.map((cc) => cc.id));

  // These code set codes can be either included or excluded
  const codeSetCodeIds = Array.from(
    new Set([...selectedCodeIds].filter((id) => !customCodeIds.has(id)))
  );

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

  const updateSelectedCodesStatus = (status: CodeResponseStatus) => {
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
          code_ids: codeSetCodeIds,
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
          clearSelections();
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

  const hasCustomCodesSelected = selectedCustomCodes.length > 0;

  const selectedCount = allSelected
    ? formatSelectedCodeCount(
        filters,
        selectedCodeIds.size,
        deselectedCodesIds.length,
        deselectedCustomCodesIds.length,
        renderedCodes.length,
        codeCounts?.data.total_code_count
      )
    : selectedCodeIds.size;
  return (
    <>
      {
        <ExclusionWarningModal
          isOpen={isOpen}
          configurationId={configurationId}
          onClose={() => setIsOpen(false)}
          updateCodesToExcluded={() => updateSelectedCodesStatus('Excluded')}
          allSelected={allSelected}
          renderedCodes={renderedCodes}
          selectedCodeIds={selectedCodeIds}
          selectedCustomCodeIds={customCodeIds}
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
                if (customCodeIds.size === 0) {
                  updateSelectedCodesStatus('Excluded');
                } else {
                  setIsOpen(true);
                }
              }}
            >
              Exclude
            </Button>
            {hasCustomCodesSelected ? (
              <CustomCodeDeletionMenu
                configurationId={configurationId}
                clearSelections={clearSelections}
                allSelected={allSelected}
                selectedCustomCodeIds={selectedCustomCodes.map((c) => c.id)}
                deselectedCustomCodeIds={deselectedCustomCodesIds}
                renderedCodesCount={renderedCodes.length}
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
  allSelected: boolean;
  clearSelections: () => void;
  selectedCustomCodeIds: string[];
  deselectedCustomCodeIds: string[];
  renderedCodesCount: number;
}

function CustomCodeDeletionMenu({
  configurationId,
  clearSelections,
  allSelected,
  selectedCustomCodeIds,
  deselectedCustomCodeIds,
  renderedCodesCount,
}: CustomCodeDeletionMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { data: codeCounts } = useGetCodeCounts(configurationId);

  let totalCustomCodes = selectedCustomCodeIds.length;
  if (allSelected && codeCounts?.data.total_custom_codes_count) {
    totalCustomCodes = codeCounts.data.total_custom_codes_count;
  }

  const deletePastCursor =
    allSelected && renderedCodesCount > CodesLimitResponseValue.codes_limit;

  const customCodesToDeleteCount = deletePastCursor
    ? totalCustomCodes - deselectedCustomCodeIds.length
    : selectedCustomCodeIds.length;

  return (
    <>
      <CustomCodeDeletionModal
        configurationId={configurationId}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        clearSelections={clearSelections}
        totalCustomCodes={totalCustomCodes}
        selectedCustomCodeIds={selectedCustomCodeIds}
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
  clearSelections: () => void;
  totalCustomCodes: number;
  selectedCustomCodeIds: string[];
  deselectedCustomCodeIds: string[];
  deletePastCursor: boolean;
  customCodesToDeleteCount: number;
}

function CustomCodeDeletionModal({
  isOpen,
  onClose,
  configurationId,
  clearSelections,
  deletePastCursor,
  selectedCustomCodeIds,
  deselectedCustomCodeIds,
  customCodesToDeleteCount,
}: CustomCodeDeletionModalProps) {
  const queryClient = useQueryClient();
  const { mutate } = useDeleteCustomCodes();
  const toast = useToast();

  const deleteCustomCodes = () => {
    mutate(
      {
        configurationId,
        data: {
          ids: selectedCustomCodeIds,
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
          clearSelections();
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
  total_custom_codes_count: number
): CountResult {
  if (
    allSelected &&
    renderedCodes.length > CodesLimitResponseValue.codes_limit
  ) {
    // If in the all selected case, start with the totals as fetched from the
    // code counts hook and tally any custom codes we've selected. Forbid exclusion
    // only if we've down-selected to a subset with only custom codes
    const deselectedCodeCount = renderedCodes.filter(
      (c) => !selectedCodeIds.has(c.id)
    ).length;

    const totalCodeCount = total_code_count;
    const totalCustomCodeCount = total_custom_codes_count;

    const excludeableCodeCount =
      totalCodeCount - deselectedCodeCount - totalCustomCodeCount;

    return {
      totalCodeCount,
      totalCustomCodeCount,
      excludeableCodeCount,
      exclusionForbidden: excludeableCodeCount <= 0,
    };
  }

  // If in the progressive section case, start with the number of selected codes
  // and forbid exclusion if they're all custom codes.
  const totalCodeCount = selectedCodeIds.size;
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
  allSelected: boolean;
  renderedCodes: CodeResponse[];
  selectedCodeIds: Set<string>;
  selectedCustomCodeIds: Set<string>;
}

function ExclusionWarningModal({
  configurationId,
  isOpen,
  onClose,
  updateCodesToExcluded,
  allSelected,
  renderedCodes,
  selectedCodeIds,
  selectedCustomCodeIds,
}: ExclusionWarningModalProps) {
  const {
    data: codeCounts,
    isPending,
    isError,
  } = useGetCodeCounts(configurationId);

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
    codeCounts?.data.total_custom_codes_count
  );

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
          <p className="border-l-3! border-l-[#d54309] bg-[#fdf3f2] px-4 py-3">
            {totalCustomCodeCount} custom codes can't be excluded. Custom codes
            can only be deleted to remove them from this configuration.
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
  filters: CodeFilters,
  selectedCodeCount: number,
  deselectedCodesCount: number,
  deselectedCustomCodesCount: number,
  renderedCodeCount: number,
  totalCodeCount?: number
): string {
  // If the rendered code count is under the pagination limit, just return
  // the selected values
  if (renderedCodeCount < CodesLimitResponseValue.codes_limit) {
    return selectedCodeCount.toString();
  }

  // Otherwise, check the search filtering and apply specific formatting
  // in the > pagination case
  if (filters.search) {
    return selectedCodeCount > CodesLimitResponseValue.codes_limit
      ? `${CodesLimitResponseValue.codes_limit}+`
      : selectedCodeCount.toString();
  }

  // Otherwise, check the active filters and tabulate the values
  const hasFilterEntry = (arr?: { count?: number }[]) => arr && arr.length > 0;

  const atLeastOneFilterActive =
    hasFilterEntry(filters.codeSystems) ||
    hasFilterEntry(filters.sources) ||
    hasFilterEntry(filters.statuses);

  if (!atLeastOneFilterActive) {
    return totalCodeCount
      ? (
          totalCodeCount -
          deselectedCodesCount -
          deselectedCustomCodesCount
        ).toString()
      : 'All ';
  }

  // Calculate total count across active array filters
  const sumCounts = (items?: { count?: number }[]) =>
    items?.reduce((acc, item) => acc + (item.count ?? 0), 0) ?? 0;

  const totalCount =
    sumCounts(filters.codeSystems) +
    sumCounts(filters.sources) +
    sumCounts(filters.statuses);

  return (totalCount - deselectedCodesCount).toString();
}
