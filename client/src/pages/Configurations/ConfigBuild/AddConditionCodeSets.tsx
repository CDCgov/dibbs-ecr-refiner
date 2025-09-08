/**
 * AddConditionCodeSetsDrawer: Main container component for adding condition code sets to a configuration.
 * Uses a Drawer UI to present a searchable list of conditions, each with controls to add or remove their association.
 * Delegates individual code set row UI to the ConditionCodeSet component.
 */
import React, { useState } from 'react';
import Drawer from '../../../components/Drawer';
import ConditionCodeSet from './ConditionCodeSet';
import { Link } from 'react-router';
import { GetConditionsWithAssociationResponse } from '../../../api/schemas';
import {
  getGetConfigurationQueryKey,
  useAssociateConditionWithConfiguration,
  useDisassociateConditionWithConfiguration,
} from '../../../api/configurations/configurations';
import { useToast } from '../../../hooks/useToast';
import { useQueryClient } from '@tanstack/react-query';
import { getGetConditionsByConfigurationQueryKey } from '../../../api/conditions/conditions';
import { highlightMatches } from '../../../utils/highlight';
import { stringify } from 'orval';

type AddConditionCodeSetsDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
  conditions: GetConditionsWithAssociationResponse[];
  configurationId: string;
};

/**
 * Drawer to add condition code sets to a configuration.
 */
const AddConditionCodeSetsDrawer: React.FC<AddConditionCodeSetsDrawerProps> = ({
  isOpen,
  onClose,
  configurationId,
  conditions,
}: AddConditionCodeSetsDrawerProps) => {
  const [searchTerm, setSearchTerm] = useState('');

  // Search and highlight logic
  const filteredConditions = searchTerm
    ? conditions.filter((cond) =>
        cond.display_name.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : conditions;

  const { mutateAsync: associateMutation } =
    useAssociateConditionWithConfiguration();
  const { mutateAsync: disassociateMutation } =
    useDisassociateConditionWithConfiguration();

  const showToast = useToast();
  const queryClient = useQueryClient();

  // Add/remove handlers
  async function handleAssociate(conditionId: string) {
    await associateMutation(
      {
        configurationId,
        data: { condition_id: conditionId },
      },
      {
        onSuccess: async (resp) => {
          showToast({
            heading: 'Condition added',
            body: resp.data.condition_name,
          });
          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationId),
          });
          await queryClient.invalidateQueries({
            queryKey: getGetConditionsByConfigurationQueryKey(configurationId),
          });
        },
      }
    );
  }

  async function handleDisassociate(conditionId: string) {
    await disassociateMutation(
      {
        configurationId,
        conditionId,
      },
      {
        onSuccess: async (resp) => {
          showToast({
            heading: 'Condition removed',
            body: resp.data.condition_name,
          });
          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationId),
          });
          await queryClient.invalidateQueries({
            queryKey: getGetConditionsByConfigurationQueryKey(configurationId),
          });
        },
        onError: (error) => {
          const errorDetail =
            stringify(error?.response?.data?.detail) ||
            error.message ||
            'Unknown error';
          showToast({
            variant: 'error',
            heading: 'Error removing condition',
            body: errorDetail,
          });
        },
      }
    );
  }

  return (
    <Drawer
      title="Add condition code sets"
      subtitle={
        <p className="!pt-2">
          Codes relevant to each condition are grouped together. These code sets
          are derived from the{' '}
          <Link
            to={'https://tes.tools.aimsplatform.org'}
            className="text-blue-cool-60 font-bold"
          >
            TES (Terminology Exchange Service)
          </Link>
          .
        </p>
      }
      isOpen={isOpen}
      searchPlaceholder="Search by condition name"
      onSearch={setSearchTerm}
      onClose={onClose}
      drawerWidth="35%"
    >
      <div className="flex h-full flex-col">
        <ol className="flex-grow overflow-y-auto">
          {filteredConditions.map(
            (condition: GetConditionsWithAssociationResponse, i: number) => {
              const highlight = searchTerm
                ? highlightMatches(
                    condition.display_name,
                    [
                      {
                        indices: [
                          [
                            condition.display_name
                              .toLowerCase()
                              .indexOf(searchTerm.toLowerCase()),
                            condition.display_name
                              .toLowerCase()
                              .indexOf(searchTerm.toLowerCase()) +
                              searchTerm.length -
                              1,
                          ],
                        ],
                        key: 'display_name',
                        value: condition.display_name,
                      },
                    ],
                    'display_name'
                  )
                : undefined;
              const key = condition.id
                ? condition.id
                : `${condition.display_name}-${i}`;
              return (
                <ConditionCodeSet
                  key={key}
                  display_name={condition.display_name}
                  associated={condition.associated}
                  configurationId={configurationId}
                  onAssociate={async () => {
                    await handleAssociate(condition.id);
                  }}
                  onDisassociate={async () => {
                    await handleDisassociate(condition.id);
                  }}
                  highlight={highlight}
                />
              );
            }
          )}
        </ol>
      </div>
    </Drawer>
  );
};

export default AddConditionCodeSetsDrawer;
