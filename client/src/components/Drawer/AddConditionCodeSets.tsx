import React, { useState } from 'react';
import { Button } from '../Button';
import Drawer from '.';
import { Link } from 'react-router';

type ConditionCodeSetsProps = {
  isOpen: boolean;
  onClose: () => void;
  onSearch: (searchFilter: string) => void;
  codeSets: ConditionCodeSetProps[];
  configurationId: string;
};

interface ConditionCodeSetProps {
  display_name: string;
  id: string;
  associated: boolean;
  configurationId: string;
}

const ConditionCodeSet: React.FC<ConditionCodeSetProps> = ({
  display_name,
  id,
  configurationId,
  associated,
}) => {
  const [showAddButton, setShowAddButton] = useState(associated);
  const [isButtonToggled, setButtonToggled] = useState(associated);

  return (
    <div
      className="flex h-16 items-center justify-between rounded-md p-4 hover:bg-white"
      onMouseEnter={() => setShowAddButton(true)}
      onMouseLeave={() => {
        if (!isButtonToggled) setShowAddButton(false);
      }}
      onFocus={() => setShowAddButton(true)}
      onBlur={() => {
        if (!isButtonToggled) setShowAddButton(false);
      }}
      onClick={() => {
        setButtonToggled(!isButtonToggled);
        setShowAddButton(true);
        console.log(configurationId);
      }}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          setButtonToggled(!isButtonToggled);
          console.log(configurationId);
        }
      }}
      tabIndex={0}
    >
      <p>{display_name}</p>
      {showAddButton && (
        <Button
          variant={isButtonToggled ? 'selected' : 'primary'}
          onClick={(e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
            e.stopPropagation();
            setButtonToggled(!isButtonToggled);
            setShowAddButton(true);
            console.log(configurationId);
          }}
          tabIndex={-1}
        >
          {isButtonToggled ? 'Added' : 'Add'}
        </Button>
      )}
    </div>
  );
};

const AddConditionCodeSetsDrawer: React.FC<ConditionCodeSetsProps> = ({
  isOpen,
  onClose,
  onSearch,
  configurationId,
  codeSets,
}: ConditionCodeSetsProps) => {
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
      placeHolder="Search by condition name"
      onSearch={onSearch}
      onClose={onClose}
      drawerWidth="35%"
    >
      <div className="flex h-full flex-col">
        <div className="flex-grow overflow-y-auto">
          {codeSets.map((condition: ConditionCodeSetProps) => {
            return (
              <ConditionCodeSet
                key={condition.id}
                display_name={condition.display_name}
                id={condition.id}
                associated={condition.associated}
                configurationId={configurationId}
              />
            );
          })}
        </div>
      </div>
    </Drawer>
  );
};

export default AddConditionCodeSetsDrawer;
