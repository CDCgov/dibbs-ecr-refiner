/**
 * AddConditionCodeSetsDrawer: Main container component for adding condition code sets to a configuration.
 * Uses a Drawer UI to present a searchable list of conditions, each with controls to add or remove their association.
 * Delegates individual code set row UI to the ConditionCodeSet component.
 */
import React, { useState } from 'react';
import Drawer from '.';
import ConditionCodeSet from './ConditionCodeSet';
import { Link } from 'react-router';
import { GetConditionsWithAssociationResponse } from '../../api/schemas';
import {
  getGetConfigurationQueryKey,
  useAssociateConditionWithConfiguration,
  useDisassociateConditionWithConfiguration,
} from '../../api/configurations/configurations';
import { useToast } from '../../hooks/useToast';
import { useQueryClient } from '@tanstack/react-query';
import { getGetConditionsByConfigurationQueryKey } from '../../api/conditions/conditions';

type ConditionCodeSetsProps = {
  isOpen: boolean;
  onClose: () => void;
  // onSearch: (searchFilter: string) => void; // Removed unused prop
  conditions: GetConditionsWithAssociationResponse[];
  configurationId: string;
};

/**
 * Drawer to add condition code sets to a configuration.
 *
 * @param {Object} Props - A list of properties for the component
 * @param {boolean} Props.isOpen - If true, drawer is visible.
 * @param {() => void} Props.onClose - Callback to close the drawer.
 * @param {GetConditionsWithAssociationResponse[]} Props.conditions - Array of condition code sets.
 * @param {string} Props.configurationId - ID of the configuration.
 */
const AddConditionCodeSetsDrawer: React.FC<ConditionCodeSetsProps> = ({
  isOpen,
  onClose,
  // onSearch,
  configurationId,
  conditions,
}: ConditionCodeSetsProps) => {
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

  const getHighlightMatch = (name: string) => {
    if (!searchTerm) return undefined;
    const index = name.toLowerCase().indexOf(searchTerm.toLowerCase());
    if (index === -1) return undefined;
    return { start: index, end: index + searchTerm.length };
  };

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
        data: { condition_id: conditionId },
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
        <div className="flex-grow overflow-y-auto">
          {filteredConditions.map(
            (condition: GetConditionsWithAssociationResponse, i: number) => {
              const highlight = getHighlightMatch(condition.display_name);
              const key = condition.id
                ? condition.id
                : `${condition.display_name}-${i}`;
              return (
                <ConditionCodeSet
                  key={key}
                  display_name={condition.display_name}
                  associated={condition.associated}
                  configurationId={configurationId}
                  id={condition.id}
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
        </div>
      </div>
    </Drawer>
  );
};

export default AddConditionCodeSetsDrawer;
