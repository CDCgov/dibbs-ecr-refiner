/**
 * ConditionCodeSet: Renders a row for a single medical condition code set in the drawer UI.
 * Provides interactive controls for toggling association with the given configuration.
 * Focused on keyboard and mouse accessibility, with a button control and ARIA labels.
 */
import React, { useState } from 'react';
import { Button } from '../../../components/Button';

/**
 * Component representing a single condition code set row within the drawer.
 * Displays the condition name and lets users add/remove association with the configuration.
 */
interface ConditionCodeSetProps {
  conditionName: string;
  associated: boolean;
  configurationId: string;
  onAssociate: () => void;
  onDisassociate: () => void;
  highlight?: React.ReactNode;
}

const ConditionCodeSet: React.FC<ConditionCodeSetProps> = ({
  conditionName,
  associated,
  onAssociate,
  onDisassociate,
  highlight,
}) => {
  const [showButton, setShowButton] = useState(true);

  React.useEffect(() => {
    setShowButton(associated);
  }, [associated]);

  return (
    <li
      className="flex h-16 items-center justify-between rounded-md p-4 hover:bg-white"
      role="listitem"
      aria-label={conditionName}
      onMouseEnter={() => setShowButton(true)}
      onMouseLeave={() => {
        if (!associated) setShowButton(false);
      }}
      onFocus={() => setShowButton(true)}
      onBlur={() => {
        if (!associated) setShowButton(false);
      }}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          if (associated) {
            onDisassociate();
          } else {
            onAssociate();
          }
          setShowButton(true);
        }
      }}
    >
      <p>{highlight ? <>{highlight}</> : conditionName}</p>
      {showButton ? (
        <Button
          variant={associated ? 'selected' : 'primary'}
          aria-pressed={associated}
          aria-label={
            associated ? `Remove ${conditionName}` : `Add ${conditionName}`
          }
          onClick={(e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
            e.stopPropagation();
            if (associated) {
              onDisassociate();
            } else {
              onAssociate();
            }
            setShowButton(true);
          }}
          tabIndex={-1}
        >
          {associated ? 'Added' : 'Add'}
        </Button>
      ) : null}
    </li>
  );
};

export default ConditionCodeSet;
