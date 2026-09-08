import { Button, ButtonProps } from '@components/Button';
import { useState } from 'react';
import { CustomCodeModal } from './CustomCodeModal';
import { useGetCustomCode } from '../../../../api/configurations/configurations';

type EditCustomCodeButtonProps = Pick<ButtonProps, 'disabled'> & {
  configurationId: string;
  id: string;
};

export function EditCustomCodeButton({
  configurationId,
  id,
  disabled,
}: EditCustomCodeButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { data: code, refetch } = useGetCustomCode(configurationId, id, {
    query: {
      enabled: false,
    },
  });

  return (
    <>
      <Button
        className="text-blue-cool-60 text-sm! font-semibold hover:cursor-pointer hover:underline"
        variant="unstyled"
        aria-label="Edit custom code"
        disabled={disabled}
        onClick={async () => {
          await refetch();
          setIsOpen(true);
        }}
      >
        Edit
      </Button>
      <CustomCodeModal
        configurationId={configurationId}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        setIsOpen={setIsOpen}
        selectedCustomCode={code?.data ?? null}
      />
    </>
  );
}
