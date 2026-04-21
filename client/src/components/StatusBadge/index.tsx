import React, { useState } from 'react';
import { Modal } from '@components/Modal';
import { Button } from '@components/Button';

// Define the enum for badge status (TODO below)
export enum BadgeStatus {
  NotExpanded = 'not_expanded',
  PartiallyIncomplete = 'partially_incomplete',
  FullyComplete = 'fully_complete',
}

// TODO: Status will eventually come from the server response instead of this enum.

export interface StatusBadgeProps {
  text: string;
  status: BadgeStatus;
  detailsContent: React.ReactNode;
  className?: string;
}

const BG_BY_STATUS: Record<BadgeStatus, string> = {
  [BadgeStatus.NotExpanded]: 'bg-red-400',
  [BadgeStatus.PartiallyIncomplete]: 'bg-yellow-300',
  [BadgeStatus.FullyComplete]: 'bg-green-300',
};

export const StatusBadge = ({
  text,
  status,
  detailsContent,
  className = '',
}: StatusBadgeProps) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <span className="inline-flex items-center">
      <span
        className={`rounded-full px-3 py-1 font-medium text-black lowercase ${BG_BY_STATUS[status]} ${className} `}
        data-testid="status-badge"
      >
        {text}
      </span>
      <Button
        variant="tertiary"
        onClick={() => setIsOpen(true)}
        aria-label="Open details modal"
      >
        Details
      </Button>
      {/* Modal opens when Details is clicked */}
      {isOpen && (
        <Modal open={isOpen} onClose={() => setIsOpen(false)}>
          <div className="p-4">{detailsContent}</div>
        </Modal>
      )}
    </span>
  );
};
