import React, { useState } from 'react';
import { Button } from '../../../components/Button';
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
  const [showButton, setShowButton] = useState(false);

  const { mutate: associateMutation } =
    useAssociateConditionWithConfiguration();
  const { mutate: disassociateMutation } =
    useDisassociateConditionWithConfiguration();

  const showToast = useToast();
  const queryClient = useQueryClient();
  const formatError = useApiErrorFormatter();

  React.useEffect(() => {
    setShowButton(condition.associated);
  }, [condition.associated]);

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
    setShowButton(true);
  }

  const isDefault =
    condition.display_name === reportable_condition_display_name;
  return (
    <li
      className={classNames(
        'flex h-16 items-center justify-between rounded-md p-4 hover:bg-white',
        {
          'cursor-pointer': !isDefault,
        }
      )}
      role="listitem"
      onClick={(e) => {
        e.stopPropagation();
        if (isDefault) return;
        onClick(condition.associated);
      }}
      onMouseEnter={() => setShowButton(true)}
      onMouseLeave={() => {
        if (!condition.associated) setShowButton(false);
      }}
      onFocus={() => setShowButton(true)}
      onBlur={() => {
        if (!condition.associated) setShowButton(false);
      }}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          onClick(condition.associated);
        }
      }}
    >
      <p>{highlight ? <>{highlight}</> : condition.display_name}</p>
      {showButton ? (
        isDefault ? (
          <span className="text-bold mr-0! w-20! text-black">Default</span>
        ) : condition.associated ? (
          <Button
            variant="secondary"
            aria-pressed={true}
            aria-label={`Remove ${condition.display_name}`}
            className="mr-0! w-20!"
            onClick={(e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
              e.stopPropagation();
              onClick(condition.associated);
            }}
            tabIndex={-1}
            disabled={disabled}
          >
            Remove
          </Button>
        ) : (
          <Button
            variant="primary"
            aria-pressed={false}
            aria-label={`Add ${condition.display_name}`}
            className="mr-0! w-20!"
            onClick={(e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
              e.stopPropagation();
              onClick(condition.associated);
            }}
            tabIndex={-1}
            disabled={disabled}
          >
            Add
          </Button>
        )
      ) : null}
    </li>
  );
}
