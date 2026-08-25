import { Button, ButtonProps } from '@components/Button';
import React, { useState } from 'react';
import { CustomCodeModal } from './CustomCodeModal';
import { Menu, MenuButton, MenuItem } from '@headlessui/react';
import { BaseMenuItems } from '@components/Dropdown';

type AddCustomCodeButtonProps = Pick<ButtonProps, 'disabled'> & {
  configurationId: string;
  setIsUploadingCustomCodes: React.Dispatch<React.SetStateAction<boolean>>;
};

export function AddCustomCodeButton({
  configurationId,
  disabled,
  setIsUploadingCustomCodes,
}: AddCustomCodeButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <>
      <Menu as="div">
        <MenuButton
          className="text-violet-warm-60 flex h-8 flex-row items-center gap-2 rounded-md border-2! bg-white px-2 text-sm! font-bold whitespace-nowrap hover:cursor-pointer hover:bg-[#f9f4f9]!"
          aria-label="Add custom code"
          disabled={disabled}
        >
          <span>Add custom code</span>
          <span aria-hidden className="flex flex-row gap-3">
            <span className="opacity-40">|</span>
            <DownArrow />
          </span>
        </MenuButton>
        <BaseMenuItems
          anchor="bottom end"
          className="ring-opacity-5 border-gray-cool-10 text-md mt-1 flex w-60 flex-col items-start rounded-md bg-white shadow-lg focus-within:outline-none!"
        >
          <MenuItem>
            <MenuItemButton onClick={() => setIsOpen(true)}>
              Add a single code
            </MenuItemButton>
          </MenuItem>
          <div aria-hidden className="bg-gray-cool-10 my-1 h-px w-full" />
          <MenuItem>
            <MenuItemButton onClick={() => setIsUploadingCustomCodes(true)}>
              Import codes from CSV
            </MenuItemButton>
          </MenuItem>
        </BaseMenuItems>
      </Menu>
      <CustomCodeModal
        configurationId={configurationId}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        setIsOpen={setIsOpen}
        selectedCustomCode={null}
      />
    </>
  );
}

interface MenuItemButtonProps {
  onClick: () => void;
  children: React.ReactNode;
}
function MenuItemButton({ onClick, children }: MenuItemButtonProps) {
  return (
    <Button
      className="hover:bg-blue-cool-5 flex w-full p-3 hover:cursor-pointer"
      onClick={onClick}
      variant="unstyled"
    >
      {children}
    </Button>
  );
}

function DownArrow() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="#864381">
      <path d="M7 10l5 5 5-5z" />
    </svg>
  );
}
