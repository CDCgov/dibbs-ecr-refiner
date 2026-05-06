import { useState } from 'react';
import {
  Modal,
  ModalBody,
  ModalHeader,
  ModalTitle,
  ModalFooter,
} from '@components/Modal';
import { Button } from '@components/Button';
import { CodeSetStatus, CompletenessStatus } from '../../../../api/schemas';
import classNames from 'classnames';

export interface CompletenessStatusBadgeProps {
  completenessStatus: CompletenessStatus;
}

export function CompletenessStatusBadge({
  completenessStatus,
}: CompletenessStatusBadgeProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div>
      <div className="flex flex-row items-center gap-2">
        <Badge status={completenessStatus.code_set_status} />
        <Button
          variant="tertiary"
          onClick={() => setIsOpen(true)}
          aria-label="Open code set completion status details modal"
          className="p-0!"
        >
          Details
        </Button>
      </div>

      {isOpen && (
        <Modal open={isOpen} onClose={() => setIsOpen(false)}>
          <ModalHeader>
            <div className="flex flex-col items-start gap-1">
              <Badge status={completenessStatus.code_set_status} />
              <ModalTitle className="sm:whitespace-nowrap">
                Code set completion details
              </ModalTitle>
              <p className="sm:text-sm sm:whitespace-nowrap">
                Understand which types of codes are expanded in this code set.
              </p>
            </div>
          </ModalHeader>

          <ModalBody>
            <table className="w-full table-fixed">
              <colgroup>
                <col className="w-2/3" />
                <col className="w-1/3" />
              </colgroup>
              <thead>
                <tr className="border-gray-cool-20 text-gray-cool-90 border-b">
                  <th className="p-2" scope="col">
                    Expanded codes
                  </th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody className="divide-gray-cool-20 divide-y">
                {completenessStatus.code_category_statuses.map((ccs) => (
                  <tr key={ccs.category}>
                    <td className="px-2 py-3">{ccs.name}</td>
                    <td className="text-center">
                      <IncludedStatus included={ccs.included} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </ModalBody>

          <ModalFooter align="center">
            <div className="mx-10 flex w-full justify-center">
              <p className="w-full text-center italic">
                Use custom codes to add codes you want to retain that are not
                included in the code set.
              </p>
            </div>
          </ModalFooter>
        </Modal>
      )}
    </div>
  );
}

interface BadgeProps {
  status: CodeSetStatus;
}
function Badge({ status }: BadgeProps) {
  return (
    <span
      aria-label={`Code set completion status: ${status}`}
      className={classNames('rounded-2xl px-2 py-1', {
        'bg-green-cool-10v': status === 'fully complete',
        'bg-red-warm-10v': status === 'not expanded',
        'bg-state-warning-lighter': status === 'partially complete',
      })}
    >
      {status}
    </span>
  );
}

interface IncludedStatusProps {
  included: boolean;
}

function IncludedStatus({ included }: IncludedStatusProps) {
  return (
    <div
      className={classNames('flex items-center gap-2', {
        'text-green-800': included,
        'text-gray-600': !included,
      })}
    >
      {included ? <CheckIcon /> : <XIcon />}
      {included ? (
        <span>included</span>
      ) : (
        <span className="italic">not included</span>
      )}
    </div>
  );
}

function CheckIcon() {
  return (
    <svg
      className="shrink-0"
      width="20"
      height="20"
      viewBox="0 0 20 20"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M7.49989 13.4749L4.02489 9.99987L2.84155 11.1749L7.49989 15.8332L17.4999 5.8332L16.3249 4.6582L7.49989 13.4749Z"
        fill="#216E1F"
      />
    </svg>
  );
}

function XIcon() {
  return (
    <svg
      className="shrink-0"
      width="20"
      height="20"
      viewBox="0 0 20 20"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M13.825 4.99951L10 8.81618L6.175 4.99951L5 6.17451L10 11.1745L15 6.17451L13.825 4.99951Z"
        fill="#565C65"
      />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M6.175 14.999L10 11.1824L13.825 14.999L15 13.824L10 8.82402L5 13.824L6.175 14.999Z"
        fill="#565C65"
      />
    </svg>
  );
}
