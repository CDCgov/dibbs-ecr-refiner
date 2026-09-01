import { Button } from '@components/Button';
import { Menu, MenuButton, MenuItem } from '@headlessui/react';
import { BaseMenuItems } from '@components/Dropdown';
import { CodeResponse, CodeResponseStatus } from '../../../api/schemas';
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

interface ControlPanelProps {
  configurationId: string;
  selectedCodeIds: Set<string>;
  selectedCustomCodes: CodeResponse[];
  clearSelections: () => void;
  allSelected: boolean;
  renderedCodes: CodeResponse[];
}
export function ControlPanel({
  configurationId,
  selectedCodeIds,
  selectedCustomCodes,
  clearSelections,
  allSelected,
  renderedCodes,
}: ControlPanelProps) {
  const toast = useToast();
  const formatError = useApiErrorFormatter();
  const queryClient = useQueryClient();
  const { mutate } = useSetCodesStatus();
  const [isOpen, setIsOpen] = useState(false);

  const { data: codeCounts } = useGetCodeCounts(configurationId);

  // These custom codes can be deleted
  const customCodeIds = new Set(selectedCustomCodes.map((cc) => cc.id));

  // These code set codes can be either included or excluded
  const codeSetCodeIds = Array.from(
    new Set([...selectedCodeIds].filter((id) => !customCodeIds.has(id)))
  );

  const updateSelectedCodesStatus = (status: CodeResponseStatus) => {
    mutate(
      {
        configurationId,
        params: {
          status: status === 'Included' ? 'included' : 'excluded',
          update_beyond_cursor: allSelected,
        },
        data: {
          code_ids: codeSetCodeIds,

          // don't touch any of the codes that are 1) rendered within
          // the cursor window and 2) that haven't been selected, since
          // those shouldn't be actioned in the bulk selection / deselection
          code_ids_to_skip: renderedCodes
            .map((c) => c.id)
            .filter((id) => !selectedCodeIds.has(id)),
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
  return (
    <>
      <ExclusionWarningModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        customCodeCount={customCodeIds.size}
        totalCodeCount={selectedCodeIds.size}
        updateCodesToExcluded={() => updateSelectedCodesStatus('Excluded')}
      />

      <div
        data-testid="control-panel"
        className="fixed bottom-5 left-1/2 -translate-x-1/2 rounded-xl bg-white px-6 py-4 shadow"
      >
        <div className="flex flex-row items-center justify-center gap-4">
          <span className="font-bold whitespace-nowrap">
            {allSelected
              ? (codeCounts?.data.total_code_count ?? 'All')
              : selectedCodeIds.size}{' '}
            selected
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
  clearSelections: () => void;
}

function CustomCodeDeletionMenu({
  configurationId,
  customCodeIds,
  clearSelections,
}: CustomCodeDeletionMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <>
      <CustomCodeDeletionModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        customCodeIds={customCodeIds}
        clearSelections={clearSelections}
        configurationId={configurationId}
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
              Delete {customCodeIds.length} custom codes
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
  configurationId: string;
  clearSelections: () => void;
}

function CustomCodeDeletionModal({
  isOpen,
  onClose,
  customCodeIds,
  configurationId,
  clearSelections,
}: CustomCodeDeletionModalProps) {
  const queryClient = useQueryClient();
  const { mutate } = useDeleteCustomCodes();
  const toast = useToast();
  const customCodeCount = customCodeIds.length;

  const deleteCustomCodes = () => {
    mutate(
      {
        configurationId,
        data: {
          ids: customCodeIds,
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
  isOpen: boolean;
  onClose: () => void;
  customCodeCount: number;
  totalCodeCount: number;
  updateCodesToExcluded: () => void;
}

function ExclusionWarningModal({
  isOpen,
  onClose,
  customCodeCount,
  totalCodeCount,
  updateCodesToExcluded,
}: ExclusionWarningModalProps) {
  const excludeableCodeCount = totalCodeCount - customCodeCount;

  const isCustomCodesOnly = excludeableCodeCount === 0;

  return (
    <Modal open={isOpen} onClose={onClose} position="center">
      <ModalHeader>
        <ModalTitle>Exclude codes</ModalTitle>
      </ModalHeader>
      <ModalBody>
        <div className="flex flex-col gap-4">
          <p>
            {isCustomCodesOnly
              ? 'None of the selected codes can be excluded.'
              : `
            ${excludeableCodeCount} of ${totalCodeCount} selected codes will be
            excluded from this configuration.`}
          </p>
          <p className="border-l-3! border-l-[#d54309] bg-[#fdf3f2] px-4 py-3">
            {customCodeCount} custom codes can't be excluded. Custom codes can
            only be deleted to remove them from this configuration.
          </p>
        </div>
      </ModalBody>
      <ModalFooter align="left">
        <div className="flex flex-row items-center gap-6">
          {isCustomCodesOnly ? null : (
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
