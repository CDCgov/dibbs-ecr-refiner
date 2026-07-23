import React, { useState } from 'react';
import { Button } from '@components/Button';
import { useQueryClient } from '@tanstack/react-query';
import classNames from 'classnames';
import {
  useAssociateConditionWithConfiguration,
  useDisassociateConditionWithConfiguration,
  getGetConfigurationQueryKey,
} from '../../../../api/configurations/configurations';
import { getGetConditionsQueryKey } from '../../../../api/conditions/conditions';
import {
  IncludedCondition,
  GetConditionsResponse,
} from '../../../../api/schemas';
import { useApiErrorFormatter } from '../../../../hooks/useErrorFormatter';
import { useToast } from '../../../../hooks/useToast';

interface ConditionCodeSetListItemProps {
  condition: IncludedCondition | GetConditionsResponse;
  configurationId: string;
  highlight?: React.ReactNode;
  reportable_condition_display_name: string;
  disabled: boolean;
  isAssociated?: boolean;
}

export function ConditionCodeSetListItem({
  condition,
  configurationId,
  highlight,
  reportable_condition_display_name,
  disabled,
  isAssociated,
}: ConditionCodeSetListItemProps) {
  const { mutate: associateMutation } =
    useAssociateConditionWithConfiguration();
  const { mutate: disassociateMutation } =
    useDisassociateConditionWithConfiguration();

  const showToast = useToast();
  const queryClient = useQueryClient();
  const formatError = useApiErrorFormatter();

  const [showButton, setShowButton] = useState(false);

  const associated = isAssociated;

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
          await queryClient.invalidateQueries({
            queryKey: getGetConditionsQueryKey(),
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
          await queryClient.invalidateQueries({
            queryKey: getGetConditionsQueryKey(),
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

  function onClick(isAssoc: boolean) {
    if (disabled) return;
    if (isAssoc) {
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
      <div className="flex items-center">
        {isDefault && (
          <span className="text-bold mr-3 text-black">Default</span>
        )}
        <Button
          variant={associated ? 'secondary' : 'primary'}
          aria-pressed={associated}
          aria-label={`${associated ? 'Remove' : 'Add'} ${condition.display_name}`}
          className={classNames('mr-0! w-20!', {
            'sr-only!': !showButton && !associated,
          })}
          onClick={() => onClick(!!associated)}
          disabled={disabled}
        >
          {associated ? 'Remove' : 'Add'}
        </Button>
      </div>
    </li>
  );
}
