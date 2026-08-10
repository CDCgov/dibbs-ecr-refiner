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
        variant="secondary"
        aria-label="Add new custom code"
        disabled={disabled}
      >
        Add custom code
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
