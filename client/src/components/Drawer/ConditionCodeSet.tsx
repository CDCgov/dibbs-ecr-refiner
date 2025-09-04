/**
 * ConditionCodeSet: Renders a row for a single medical condition code set in the drawer UI.
 * Provides interactive controls for toggling association with the given configuration.
 * Focused on keyboard and mouse accessibility, with a button control and ARIA labels.
 */
import React, { useState } from 'react';
import { Button } from '../Button';

/**
 * Component representing a single condition code set row within the drawer.
 * Displays the condition name and lets users add/remove association with the configuration.
 *
 * @param {string} display_name - The name of the condition.
 * @param {boolean} associated - Whether the code set is already associated.
 * @param {string} configurationId - ID of the configuration being edited.
 */
interface ConditionCodeSetProps {
  display_name: string;
  associated: boolean;
  configurationId: string;
  id: string;
  onAssociate: () => void;
  onDisassociate: () => void;
  highlight?: { start: number; end: number };
}

const ConditionCodeSet: React.FC<ConditionCodeSetProps> = ({
  display_name,
  associated,
  onAssociate,
  onDisassociate,
  highlight,
}) => {
  const [showButton, setShowButton] = useState(associated);

  return (
    <div
      className="flex h-16 items-center justify-between rounded-md p-4 hover:bg-white"
      role="listitem"
      aria-label={display_name}
      onMouseEnter={() => setShowButton(true)}
      onMouseLeave={() => {
        if (!associated) setShowButton(false);
      }}
      onFocus={() => setShowButton(true)}
      onBlur={() => {
        if (!associated) setShowButton(false);
      }}
      tabIndex={-1}
    >
      <p>
        {highlight ? (
          <>
            {display_name.substring(0, highlight.start)}
            <mark>
              {display_name.substring(highlight.start, highlight.end)}
            </mark>
            {display_name.substring(highlight.end)}
          </>
        ) : (
          display_name
        )}
      </p>
      {showButton && (
        <Button
          variant={associated ? 'selected' : 'primary'}
          aria-pressed={associated}
          aria-label={
            associated ? `Remove ${display_name}` : `Add ${display_name}`
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
          tabIndex={0}
        >
          {associated ? 'Added' : 'Add'}
        </Button>
      )}
    </div>
  );
};

export default ConditionCodeSet;
