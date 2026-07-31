import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import {
  useDeleteCustomCodeFromConfiguration,
  getGetConfigurationQueryKey,
} from '../../../../api/configurations/configurations';
import { CustomCodeResponse } from '../../../../api/schemas';
import { useToast } from '../../../../hooks/useToast';
import { Button } from '@components/Button';
import { CustomCodeModal } from './CustomCodeModal';

interface CustomCodesDetailProps {
  configurationId: string;
  customCodes: CustomCodeResponse[];
  disabled: boolean;
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

export function CustomCodesDetail({
  configurationId,
  customCodes,
  disabled,
  isOpen,
  setIsOpen,
}: CustomCodesDetailProps) {
  const { mutate: deleteCode } = useDeleteCustomCodeFromConfiguration();
  const [selectedCustomCode, setSelectedCustomCode] =
    useState<CustomCodeResponse | null>(null);
  const queryClient = useQueryClient();
  const showToast = useToast();

  const resetModal = () => {
    setSelectedCustomCode(null);
  };

  return (
    <div role="region">
      <table className="mt-6! w-full border-separate">
        <thead className="sr-only">
          <tr>
            <th>Custom code</th>
            <th>Custom code system</th>
            <th>Custom Display name</th>
            <th>Modify the custom code</th>
          </tr>
        </thead>
        <tbody>
          {customCodes.map((customCode) => (
            <tr
              key={customCode.code + customCode.system_id}
              className="align-middle"
            >
              <td className="w-1/6 pb-6">{customCode.code}</td>
              <td className="text-gray-cool-60 w-1/6 pb-6">
                {customCode.system_name}
              </td>
              <td className="w-1/6 pb-6">{customCode.display}</td>

              <td className="flex w-1/2 justify-end pb-6 whitespace-nowrap">
                {!disabled && (
                  <div className="flex flex-row gap-2">
                    <Button
                      variant="tertiary"
                      onClick={() => {
                        if (disabled) return;
                        setSelectedCustomCode(customCode);
                        setIsOpen(true);
                      }}
                      aria-label={`Edit custom code ${customCode.display}`}
                      disabled={disabled}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="tertiary"
                      aria-label={`Delete custom code ${customCode.display}`}
                      onClick={() => {
                        if (disabled) return;
                        deleteCode(
                          {
                            configurationId: configurationId,
                            id: customCode.id,
                          },
                          {
                            onSuccess: async () => {
                              await queryClient.invalidateQueries({
                                queryKey:
                                  getGetConfigurationQueryKey(configurationId),
                              });
                              showToast({
                                heading: 'Deleted code',
                                body: customCode.code,
                              });
                            },
                          }
                        );
                      }}
                    >
                      Delete
                    </Button>
                    <div className="sr-only">
                      Editing actions aren't available for previous versions
                    </div>
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <CustomCodeModal
        isOpen={isOpen}
        setIsOpen={setIsOpen}
        configurationId={configurationId}
        selectedCustomCode={selectedCustomCode}
        onClose={resetModal}
      />
    </div>
  );
}
