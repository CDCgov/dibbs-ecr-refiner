import { useState } from 'react';
import { Drawer } from '../../../components/Drawer';
import { ConditionCodeSetListItem } from './ConditionCodeSetListItem';
import { highlightMatches } from '../../../utils';
import { IncludedCondition } from '../../../api/schemas';
import { TesLink } from '../TesLink';

type AddConditionCodeSetsDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
  conditions: IncludedCondition[];
  configurationId: string;
  reportable_condition_display_name: string;
  disabled?: boolean;
};

export function AddConditionCodeSetsDrawer({
  isOpen,
  onClose,
  configurationId,
  conditions,
  reportable_condition_display_name,
  disabled,
}: AddConditionCodeSetsDrawerProps) {
  const [searchTerm, setSearchTerm] = useState('');

  // Search and highlight logic
  const filteredConditions = searchTerm
    ? conditions.filter((cond) =>
        cond.display_name.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : conditions;

  return (
    <Drawer
      title="Add condition code sets"
      subtitle={
        <p className="pt-2!">
          Codes relevant to each condition are grouped together. These code sets
          are derived from the <TesLink />
        </p>
      }
      isOpen={isOpen}
      searchPlaceholder="Search by condition name"
      onSearch={setSearchTerm}
      onClose={onClose}
      drawerWidth="35%"
    >
      <div className="flex h-full flex-col">
        <ol className="grow overflow-y-auto">
          {filteredConditions.map((condition: IncludedCondition, i: number) => {
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
              <ConditionCodeSetListItem
                key={key}
                condition={condition}
                configurationId={configurationId}
                highlight={highlight}
                reportable_condition_display_name={
                  reportable_condition_display_name
                }
                disabled={disabled}
              />
            );
          })}
        </ol>
      </div>
    </Drawer>
  );
}
