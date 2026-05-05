import { useState } from 'react';
import {
  Modal,
  ModalBody,
  ModalHeader,
  ModalTitle,
  ModalFooter,
} from '@components/Modal';
import { Button } from '@components/Button';
import { CompletenessStatus } from '../../../../api/schemas';
import classNames from 'classnames';

export interface StatusBadgeProps {
  completenessStatus: CompletenessStatus;
}

export function StatusBadge({
  completenessStatus: coverage,
}: StatusBadgeProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div>
      <div className="flex flex-row items-center gap-2">
        <p
          className={classNames(
            'rounded-2xl px-2 py-1',
            {
              'bg-green-200': coverage.overall_status === 'fully complete',
            },
            {
              'bg-orange-100': coverage.overall_status === 'not expanded',
            },
            {
              'bg-yellow-100': coverage.overall_status === 'partially complete',
            }
          )}
        >
          {coverage.overall_status}
        </p>
        <Button
          variant="tertiary"
          onClick={() => setIsOpen(true)}
          aria-label="Open details modal"
          className="p-0!"
        >
          Details
        </Button>
      </div>

      {isOpen && (
        <Modal open={isOpen} onClose={() => setIsOpen(false)}>
          <ModalHeader>
            <ModalTitle>Code set details</ModalTitle>
            <p className="italic">
              Understand what is and is not included in this code set.
            </p>
          </ModalHeader>

          <ModalBody>
            <p>wip</p>
          </ModalBody>

          <ModalFooter>
            <p className="w-5/6">
              Use custom codes to add codes you want to retain that are not
              included in the code set.
            </p>
            <p className="text-sm font-bold">
              Updated on {coverage.last_updated_at}
            </p>
          </ModalFooter>
        </Modal>
      )}
    </div>
  );
}
