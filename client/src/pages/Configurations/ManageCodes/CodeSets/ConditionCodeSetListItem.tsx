import React from 'react';
import { Button } from '@components/Button';
import { useQueryClient } from '@tanstack/react-query';
import classNames from 'classnames';
import {
  useAssociateConditionWithConfiguration,
  useDisassociateConditionWithConfiguration,
  getGetConfigurationQueryKey,
  getGetCodeCountsQueryKey,
  getGetCodesInfiniteQueryKey,
  getGetCodeFiltersQueryKey,
} from '../../../../api/configurations/configurations';
import { IncludedCondition } from '../../../../api/schemas';
import { useApiErrorFormatter } from '../../../../hooks/useErrorFormatter';
import { useToast } from '../../../../hooks/useToast';
import { CompletenessStatusBadge } from './CompletenessStatusBadge';

interface ConditionCodeSetListItemProps {
  condition: IncludedCondition;
  configurationId: string;
  showHiddenElements: boolean;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
  onFocus: () => void;
  highlight?: React.ReactNode;
  reportableConditionDisplayName: string;
  disabled: boolean;
}

export function ConditionCodeSetListItem({
  condition,
  configurationId,
  showHiddenElements,
  onMouseEnter,
  onMouseLeave,
  onFocus,
  highlight,
  reportableConditionDisplayName,
  disabled,
}: ConditionCodeSetListItemProps) {
  const { mutate: associateMutation } =
    useAssociateConditionWithConfiguration();
  const { mutate: disassociateMutation } =
    useDisassociateConditionWithConfiguration();

  const showToast = useToast();
  const queryClient = useQueryClient();
  const formatError = useApiErrorFormatter();

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
            queryKey: getGetCodesInfiniteQueryKey(configurationId),
          });
          await queryClient.invalidateQueries({
            queryKey: getGetCodeCountsQueryKey(configurationId),
          });
          await queryClient.invalidateQueries({
            queryKey: getGetCodeFiltersQueryKey(configurationId),
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
            queryKey: getGetCodesInfiniteQueryKey(configurationId),
          });
          await queryClient.invalidateQueries({
            queryKey: getGetCodeCountsQueryKey(configurationId),
          });
          await queryClient.invalidateQueries({
            queryKey: getGetCodeFiltersQueryKey(configurationId),
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

  const isDefault = condition.display_name === reportableConditionDisplayName;
  return (
    <li
      className={classNames(
        'flex items-center justify-between rounded-md p-4 hover:bg-white'
      )}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onFocus={onFocus}
    >
      <div className="flex w-full flex-row items-center justify-between">
        <div className="flex flex-col gap-2">
          <p>{highlight ? <>{highlight}</> : condition.display_name}</p>
          <div className="flex flex-row items-center justify-start gap-1 text-sm!">
            <span
              className={classNames({
                'sr-only!': !showHiddenElements,
              })}
            >
              <CompletenessStatusBadge
                conditionId={condition.id}
                status={condition.code_set_status}
              />
            </span>
          </div>
        </div>
        {isDefault ? (
          <span className="text-bold mr-3 text-black">Default</span>
        ) : (
          <Button
            variant={condition.associated ? 'secondary' : 'primary'}
            aria-pressed={condition.associated}
            aria-label={`${condition.associated ? 'Remove' : 'Add'} ${condition.display_name}`}
            className={classNames('mr-0! w-20!', {
              'sr-only!': !showHiddenElements && !condition.associated,
            })}
            onClick={() => onClick(condition.associated)}
            disabled={disabled}
          >
            {condition.associated ? 'Remove' : 'Add'}
          </Button>
        )}
      </div>
    </li>
  );
}
