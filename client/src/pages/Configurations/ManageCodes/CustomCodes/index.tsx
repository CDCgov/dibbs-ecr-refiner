import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import {
  useDeleteCustomCodeFromConfiguration,
  getGetConfigurationQueryKey,
  getGetCodesInfiniteQueryKey,
  getGetCodeCountsQueryKey,
} from '../../../../api/configurations/configurations';
import { CustomCodeResponse } from '../../../../api/schemas';
import { useToast } from '../../../../hooks/useToast';
import { Button } from '@components/Button';
import {
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
} from '@components/Table';
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
      <Table className="mt-6! border-separate">
        <TableHead className="sr-only">
          <TableRow>
            <TableHeaderCell>Custom code</TableHeaderCell>
            <TableHeaderCell>Custom code system</TableHeaderCell>
            <TableHeaderCell>Custom Display name</TableHeaderCell>
            <TableHeaderCell>Modify the custom code</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {customCodes.map((customCode) => (
            <TableRow
              key={customCode.code + customCode.system_id}
              className="align-middle"
            >
              <TableCell className="w-1/6 pb-6">{customCode.code}</TableCell>
              <TableCell className="text-gray-cool-60 w-1/6 pb-6">
                {customCode.system_name}
              </TableCell>
              <TableCell className="w-1/6 pb-6">{customCode.display}</TableCell>

              <TableCell className="flex w-1/2 justify-end pb-6 whitespace-nowrap">
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
                              await queryClient.invalidateQueries({
                                queryKey:
                                  getGetCodesInfiniteQueryKey(configurationId),
                              });
                              await queryClient.invalidateQueries({
                                queryKey:
                                  getGetCodeCountsQueryKey(configurationId),
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
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
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
