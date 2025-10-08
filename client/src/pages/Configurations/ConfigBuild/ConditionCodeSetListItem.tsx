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
import { Spinner } from '../../../components/Spinner';

interface ConditionCodeSetListItemProps {
  condition: IncludedCondition;
  configurationId: string;
  highlight?: React.ReactNode;
}

export function ConditionCodeSetListItem({
  condition,
  configurationId,
  highlight,
}: ConditionCodeSetListItemProps) {
  const [showButton, setShowButton] = useState(false);
  const [isRefreshingConditionList, setIsRefreshingConditionList] =
    useState(false);

  const { mutate: associateMutation, isPending: isAssociatePending } =
    useAssociateConditionWithConfiguration();
  const { mutate: disassociateMutation, isPending: isDissociatePending } =
    useDisassociateConditionWithConfiguration();

  const isLoading =
    isAssociatePending || isDissociatePending || isRefreshingConditionList;

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
            heading: 'Condition added',
            body: resp.data.condition_name,
          });

          setIsRefreshingConditionList(true);
          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationId),
          });
          setIsRefreshingConditionList(false);
        },
        onError: (error) => {
          setIsRefreshingConditionList(false);
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
            heading: 'Condition removed',
            body: resp.data.condition_name,
          });
          setIsRefreshingConditionList(true);
          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationId),
          });
          setIsRefreshingConditionList(false);
        },
        onError: (error) => {
          setIsRefreshingConditionList(false);
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
    if (associated) {
      handleDisassociate();
    } else {
      handleAssociate();
    }
    setShowButton(true);
  }

  return (
    <li
      className="flex h-16 cursor-pointer items-center justify-between rounded-md p-4 hover:bg-white"
      role="listitem"
      onClick={(e) => {
        e.stopPropagation();
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
      {isLoading ? (
        <Spinner />
      ) : showButton ? (
        <Button
          variant={condition.associated ? 'selected' : 'primary'}
          aria-pressed={condition.associated}
          aria-label={
            condition.associated
              ? `Remove ${condition.display_name}`
              : `Add ${condition.display_name}`
          }
          className="!mr-0 !w-[80px]"
          onClick={(e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
            e.stopPropagation();
            onClick(condition.associated);
          }}
          tabIndex={-1}
        >
          {condition.associated ? 'Added' : 'Add'}
        </Button>
      ) : null}
    </li>
  );
}
