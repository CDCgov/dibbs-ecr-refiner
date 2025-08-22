import React, { useState } from 'react';
import { Button } from '../Button';

interface ConditionItemProps {
  conditionName: string;
}

const ConditionItem: React.FC<ConditionItemProps> = ({ conditionName }) => {
  const [showAddButton, setShowAddButton] = useState(false);
  const [isButtonToggled, setButtonToggled] = useState(false);

  return (
    <div
      className="flex h-16 items-center justify-between rounded-md p-4 transition-colors hover:bg-white"
      onMouseEnter={() => setShowAddButton(true)}
      onMouseLeave={() => {
        if (!isButtonToggled) setShowAddButton(false);
      }}
    >
      <p>{conditionName}</p>
      {showAddButton && (
        <Button
          variant={isButtonToggled ? 'selected' : 'primary'}
          onClick={() => {
            setButtonToggled(!isButtonToggled);
            setShowAddButton(true);
          }}
        >
          {isButtonToggled ? 'Added' : 'Add'}
        </Button>
      )}
    </div>
  );
};

export default ConditionItem;
