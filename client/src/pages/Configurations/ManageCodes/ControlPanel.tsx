import { Button } from '@components/Button';
import { Menu, MenuButton, MenuItem } from '@headlessui/react';
import { BaseMenuItems } from '@components/Dropdown';
import {
  CodeCountsResponse,
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
import { AxiosResponse } from 'axios';

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

  // These codes are "unselected" ones within the set, which we need in cases
  // where bulk selection is applied to "all but the selected" codes
  const deselectedCodes = renderedCodes
    .filter((c) => !c.is_custom)
    .map((c) => c.id)
    .filter((id) => !selectedCodeIds.has(id));

  // These codes are "unselected" ones within the set, which we need in cases
  // where bulk selection is applied to "all but the selected" codes
  const deselectedCustomCodes = renderedCodes
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
          code_ids_to_skip: deselectedCodes,
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
  const { data: codeCounts } = useGetCodeCounts(configurationId);

  const selectedCount = allSelected
    ? tallyActiveFilterCount(
        filters,
        selectedCodeIds.size,
        deselectedCodes.length,
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
          deselectedCustomCodeCount={deselectedCustomCodes.length}
          deselectedCodeCount={deselectedCodes.length}
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
                customCodeIds={selectedCustomCodes.map((cc) => cc.id)}
                clearSelections={clearSelections}
                allSelected={allSelected}
                customCodesToSkip={deselectedCustomCodes}
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
  customCodeIds: string[];
  customCodesToSkip: string[];
  allSelected: boolean;
  clearSelections: () => void;
}

function CustomCodeDeletionMenu({
  configurationId,
  customCodeIds,
  clearSelections,
  allSelected,
  customCodesToSkip,
}: CustomCodeDeletionMenuProps) {
  const [isOpen, setIsOpen] = useState(false);

  const { data: codeCounts } = useGetCodeCounts(configurationId);

  let customCodeCounts = customCodeIds.length;
  if (allSelected && codeCounts?.data.total_custom_codes_count) {
    customCodeCounts =
      codeCounts.data.total_custom_codes_count - customCodesToSkip.length;
  }

  return (
    <>
      <CustomCodeDeletionModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        customCodeIds={customCodeIds}
        clearSelections={clearSelections}
        configurationId={configurationId}
        allSelected={allSelected}
        customCodesToSkip={customCodesToSkip}
        customCodeCount={customCodeCounts}
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
              Delete {customCodeCounts} custom codes
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
  customCodeIds: string[];
  customCodesToSkip: string[];
  allSelected: boolean;
  configurationId: string;
  clearSelections: () => void;
  customCodeCount: number;
}

function CustomCodeDeletionModal({
  isOpen,
  onClose,
  customCodeIds,
  customCodesToSkip,
  allSelected,
  configurationId,
  clearSelections,
  customCodeCount,
}: CustomCodeDeletionModalProps) {
  const queryClient = useQueryClient();
  const { mutate } = useDeleteCustomCodes();
  const toast = useToast();

  const deleteCustomCodes = () => {
    mutate(
      {
        configurationId,
        data: {
          ids: customCodeIds,
          ids_to_skip: customCodesToSkip,
          delete_all: allSelected,
        },
      },
      {
        onSuccess: async () => {
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
            body: `${customCodeCount} custom codes deleted.`,
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
        <ModalTitle>{customCodeCount} custom codes will be deleted</ModalTitle>
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
            Delete {customCodeCount} codes
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

interface ExclusionWarningModalProps {
  configurationId: string;
  isOpen: boolean;
  onClose: () => void;
  deselectedCustomCodeCount: number;
  deselectedCodeCount: number;
  updateCodesToExcluded: () => void;
  allSelected: boolean;
}

function ExclusionWarningModal({
  configurationId,
  isOpen,
  onClose,
  deselectedCustomCodeCount,
  deselectedCodeCount,
  updateCodesToExcluded,
  allSelected,
}: ExclusionWarningModalProps) {
  const {
    data: codeCounts,
    isPending,
    isError,
  } = useGetCodeCounts(configurationId);
  if (isPending) return <Spinner variant="centered" />;
  if (isError) return 'Error!';

  const totalCustomCodeCount = codeCounts.data.total_custom_codes_count;
  const totalCodeCount = codeCounts.data.total_code_count;

  const excludeableCodeCount =
    totalCodeCount - deselectedCodeCount - totalCustomCodeCount;

  const isCustomCodesOnly = excludeableCodeCount <= 0;
  const exclusionForbidden = isCustomCodesOnly && !allSelected;

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
            {totalCustomCodeCount - deselectedCustomCodeCount} custom codes
            can't be excluded. Custom codes can only be deleted to remove them
            from this configuration.
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
function tallyActiveFilterCount(
  filters: CodeFilters,
  selectedCodes: number,
  deselectedCodes: number,
  totalCodeCount?: number
): string | number {
  if (filters.search) {
    return selectedCodes > CodesLimitResponseValue.codes_limit
      ? `${CodesLimitResponseValue.codes_limit}+`
      : selectedCodes;
  }

  const hasFilterEntry = (arr?: { count?: number }[]) => arr && arr.length > 0;

  const isFilterActive =
    hasFilterEntry(filters.codeSystems) ||
    hasFilterEntry(filters.sources) ||
    hasFilterEntry(filters.statuses);

  if (!isFilterActive) {
    return totalCodeCount ? totalCodeCount - deselectedCodes : 'All ';
  }

  // Calculate total count across active array filters
  const sumCounts = (items?: { count?: number }[]) =>
    items?.reduce((acc, item) => acc + (item.count ?? 0), 0) ?? 0;

  const totalCount =
    sumCounts(filters.codeSystems) +
    sumCounts(filters.sources) +
    sumCounts(filters.statuses);

  const netCount = totalCount - deselectedCodes;

  if (filters.search) {
    return totalCount > 0
      ? `${netCount} codes + all search results`
      : 'All search results';
  }

  return totalCount > 0 ? netCount.toString() : '';
}
