import React, { useState } from 'react';
import { Button } from '@components/Button';
import { useQueryClient } from '@tanstack/react-query';
import {
  useAssociateConditionWithConfiguration,
  useDisassociateConditionWithConfiguration,
  getGetConfigurationQueryKey,
} from '../../../api/configurations/configurations';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';
import { useToast } from '../../../hooks/useToast';
import { IncludedCondition } from '../../../api/schemas';
import classNames from 'classnames';

interface ConditionCodeSetListItemProps {
  condition: IncludedCondition;
  configurationId: string;
  highlight?: React.ReactNode;
  reportable_condition_display_name: string;
  disabled: boolean;
}

export function ConditionCodeSetListItem({
  condition,
  configurationId,
  highlight,
  reportable_condition_display_name,
  disabled,
}: ConditionCodeSetListItemProps) {
  const { mutate: associateMutation } =
    useAssociateConditionWithConfiguration();
  const { mutate: disassociateMutation } =
    useDisassociateConditionWithConfiguration();

  const showToast = useToast();
  const queryClient = useQueryClient();
  const formatError = useApiErrorFormatter();

  const [showButton, setShowButton] = useState(false);

  function handleAssociate() {
    associateMutation(
      {
        configurationId,
        data: { condition_id: condition.id },
      },
      {
        onSuccess: async (resp) => {
          showToast({
            heading: 'Condition code set added',
            body: resp.data.condition_name,
          });

          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationId),
          });
        },
        onError: (error) => {
          const errorDetail =
            formatError(error) || error.message || 'Unknown error';
          showToast({
            variant: 'error',
            heading: 'Error associating condition',
            body: errorDetail,
          });
        },
      }
    );
  }

  function handleDisassociate() {
    disassociateMutation(
      {
        configurationId,
        conditionId: condition.id,
      },
      {
        onSuccess: async (resp) => {
          showToast({
            heading: 'Condition code set removed',
            body: resp.data.condition_name,
          });

          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationId),
          });
        },
        onError: (error) => {
          const errorDetail =
            formatError(error) || error.message || 'Unknown error';
          showToast({
            variant: 'error',
            heading: 'Error removing condition',
            body: errorDetail,
          });
        },
      }
    );
  }

  function onClick(associated: boolean) {
    if (disabled) return;
    if (associated) {
      handleDisassociate();
    } else {
      handleAssociate();
    }
  }

  const isDefault =
    condition.display_name === reportable_condition_display_name;
  return (
    <li
      className={classNames(
        'flex h-16 items-center justify-between rounded-md p-4 hover:bg-white'
      )}
      onMouseEnter={() => setShowButton(true)}
      onMouseLeave={() => setShowButton(false)}
      onFocus={() => setShowButton(true)}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) {
          setShowButton(false);
        }
      }}
    >
      <p>{highlight ? <>{highlight}</> : condition.display_name}</p>
      {isDefault ? (
        <span className="text-bold mr-3 text-black">Default</span>
      ) : (
        <Button
          variant={condition.associated ? 'secondary' : 'primary'}
          aria-pressed={condition.associated}
          aria-label={`${condition.associated ? 'Remove' : 'Add'} ${condition.display_name}`}
          className={classNames('mr-0! w-20!', {
            'sr-only!': !showButton && !condition.associated,
          })}
          onClick={() => onClick(condition.associated)}
          disabled={disabled}
        >
          {condition.associated ? 'Remove' : 'Add'}
        </Button>
      )}
    </li>
  );
}
