import { useState } from 'react';
import {
  Modal,
  ModalBody,
  ModalHeader,
  ModalTitle,
  ModalFooter,
} from '@components/Modal';
import { Button } from '@components/Button';
import { GetConditionCode } from '../../../../api/schemas';

export interface StatusBadgeProps {
  text: string;
  status: 'incomplete' | 'partial' | 'complete';
  coverage: GetConditionCode;
  className?: string;
}

const BG_BY_STATUS: Record<string, string> = {
  incomplete: 'bg-red-400',
  partial: 'bg-yellow-300',
  complete: 'bg-green-300',
};

export const StatusBadge = ({
  text,
  status,
  coverage,
  className = '',
}: StatusBadgeProps) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="inline-flex items-center pb-4">
      <span
        className={`rounded-full px-3 py-1 font-medium text-black lowercase ${BG_BY_STATUS[status]} ${className} `}
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
          <ModalHeader>
            <span
              className={`rounded-full px-3 py-1 font-medium text-black lowercase ${BG_BY_STATUS[status]} ${className} `}
            >
              {text}
            </span>
            <ModalTitle className="mt-4">Code set details</ModalTitle>
            <p className="italic">
              Understand what is and is not included in this code set.
            </p>
          </ModalHeader>

          <ModalBody>
            <div className="flex flex-col gap-2">
              <p>{coverage.coverage_level_reason}</p>
            </div>

            <ModalFooter className="flex flex-row">
              <p className="max-w-[70%] italic">
                Use custom codes to add codes you want to retain that are not
                included in the code set.
              </p>
              <div className="text-small">
                <em className="block">
                  Updated on {coverage.coverage_level_date ?? 'n/a'}
                </em>
                <span className="block">(Version 3.0.0)</span>
              </div>
            </ModalFooter>
          </ModalBody>
        </Modal>
      )}
    </div>
  );
};
