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
      className="flex h-10 flex-row items-center justify-between py-4 text-left"
      onMouseEnter={() => setShowAddButton(true)}
      onMouseLeave={() => {
        if (!isButtonToggled) setShowAddButton(false);
      }}
    >
      <span className="py-10">{conditionName}</span>
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
