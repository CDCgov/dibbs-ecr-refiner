import { Button } from '@components/Button';
import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/react';
import { CodeResponse } from '../../../api/schemas';
import { DeleteIcon } from './DeleteIcon';

interface ControlPanelProps {
  selectedCodeIds: Set<string>;
  selectedCustomCodes: CodeResponse[];
}
export function ControlPanel({
  selectedCodeIds,
  selectedCustomCodes,
}: ControlPanelProps) {
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
          >
            Include
          </Button>
          <Button
            variant="unstyled"
            className="text-gray-cool-90 hover:bg-gray-5 rounded border-2! px-4.5 py-2 text-sm! font-bold hover:cursor-pointer"
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
