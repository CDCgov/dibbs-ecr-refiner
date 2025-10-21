import { useState } from 'react';
import Drawer from '../../../components/Drawer';
import { ConditionCodeSetListItem } from './ConditionCodeSetListItem';
import { Link } from 'react-router';
import { highlightMatches } from '../../../utils/highlight';
import { IncludedCondition } from '../../../api/schemas';

type AddConditionCodeSetsDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
  conditions: IncludedCondition[];
  configurationId: string;
  display_name: string;
};

export function AddConditionCodeSetsDrawer({
  isOpen,
  onClose,
  configurationId,
  conditions,
  display_name,
}: AddConditionCodeSetsDrawerProps) {
  const [searchTerm, setSearchTerm] = useState('');

  console.log(display_name);

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
        <p className="!pt-2">
          Codes relevant to each condition are grouped together. These code sets
          are derived from the{' '}
          <Link
            to="https://tes.tools.aimsplatform.org"
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
                display_name={display_name}
              />
            );
          })}
        </ol>
      </div>
    </Drawer>
  );
}
