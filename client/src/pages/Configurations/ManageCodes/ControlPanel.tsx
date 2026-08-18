import { Button } from '@components/Button';
import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/react';
import { CodeResponse, CodeResponseStatus } from '../../../api/schemas';
import { DeleteIcon } from './DeleteIcon';
import { useToast } from '../../../hooks/useToast';
import {
  getGetCodeCountsQueryKey,
  getGetCodeFiltersQueryKey,
  getGetCodesInfiniteQueryKey,
  useSetCodesStatus,
} from '../../../api/configurations/configurations';
import { useQueryClient } from '@tanstack/react-query';

interface ControlPanelProps {
  configurationId: string;
  selectedCodeIds: Set<string>;
  selectedCustomCodes: CodeResponse[];
  clearSelections: () => void;
}
export function ControlPanel({
  configurationId,
  selectedCodeIds,
  selectedCustomCodes,
}: ControlPanelProps) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const { mutate } = useSetCodesStatus();

  // These custom codes can be deleted
  const customCodeIds = new Set(selectedCustomCodes.map((cc) => cc.id));

  // These code set codes can be either included or excluded
  const codeSetCodeIds = Array.from(
    new Set([...selectedCodeIds].filter((id) => !customCodeIds.has(id)))
  );

  const setStatus = (status: CodeResponseStatus) => {
    mutate(
      {
        configurationId,
        params: {
          status: status === 'Included' ? 'included' : 'excluded',
        },
        data: codeSetCodeIds,
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
            heading: `Code ${status}`,
            body: `${selectedCodeIds.size} codes ${status.toLowerCase()} in this configuration.`,
          });
        },
      }
    );
  };

  const hasCustomCodesSelected = selectedCustomCodes.length > 0;
  return (
    <div className="fixed bottom-5 left-1/2 -translate-x-1/2 rounded-xl bg-white px-6 py-4 shadow">
      <div className="flex flex-row items-center justify-center gap-4">
        <span className="font-bold whitespace-nowrap">
          {selectedCodeIds.size} selected
        </span>
        <div aria-hidden className="h-8 border border-gray-400!" />
        <div className="flex flex-row gap-6">
          <Button
            variant="unstyled"
            className="text-blue-cool-50 hover:bg-blue-cool-5 rounded border-2! px-4.5 py-2 text-sm! font-bold hover:cursor-pointer"
            onClick={() => setStatus('Included')}
          >
            Include
          </Button>
          <Button
            variant="unstyled"
            className="text-gray-cool-90 hover:bg-gray-5 rounded border-2! px-4.5 py-2 text-sm! font-bold hover:cursor-pointer"
            onClick={() => setStatus('Excluded')}
          >
            Exclude
          </Button>
          {hasCustomCodesSelected ? (
            <Menu as="div" className="relative">
              <MenuButton
                as={Button}
                aria-label="More options"
                variant="unstyled"
                className="text-gray-cool-90 hover:bg-gray-5 rounded border-2! px-4 py-2 text-sm! font-bold hover:cursor-pointer"
              >
                ...
              </MenuButton>
              <MenuItems
                portal
                anchor="top end"
                className="rounded bg-white shadow-lg ring-1 ring-black/5 focus:outline-none"
              >
                <MenuItem>
                  <Button
                    variant="unstyled"
                    className="data-focus:bg-state-error-lighter text-state-error-dark flex flex-row items-center p-3 text-left text-sm! font-bold whitespace-nowrap data-focus:cursor-pointer"
                    onClick={() => {}}
                  >
                    <DeleteIcon />
                    Delete {selectedCustomCodes.length} custom codes
                  </Button>
                </MenuItem>
              </MenuItems>
            </Menu>
          ) : null}
        </div>
      </div>
    </div>
  );
}
