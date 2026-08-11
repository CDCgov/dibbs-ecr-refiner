import { Button, ButtonProps } from '@components/Button';
import { useState } from 'react';
import { CustomCodeModal } from './CustomCodeModal';

type AddCustomCodeButtonProps = Pick<ButtonProps, 'disabled'> & {
  configurationId: string;
};

export function AddCustomCodeButton({
  configurationId,
  disabled,
}: AddCustomCodeButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <>
      <Button
        onClick={() => setIsOpen(true)}
        variant="unstyled"
        className="text-violet-warm-60 flex h-8 flex-row items-center gap-2 rounded-md border-2! bg-white px-2 text-sm! font-bold hover:cursor-pointer hover:bg-[#f9f4f9]!"
        aria-label="Add new custom code"
        disabled={disabled}
      >
        <span>Add custom code</span>
        <span aria-hidden className="flex flex-row gap-3">
          <span className="opacity-40">|</span>
          <DownArrow />
        </span>
      </Button>
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

function DownArrow() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="#864381">
      <path data-dc-tpl="130" d="M7 10l5 5 5-5z" />
    </svg>
  );
}
