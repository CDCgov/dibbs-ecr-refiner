import { AuditEvent } from '../../api/schemas';
import { Table } from '@components/Table';
import { useDatetimeFormatter } from '../../hooks/UseDatetimeFormatter';
import { Button } from '@components/Button';
import { Modal, ModalBody, ModalHeader, ModalTitle } from '@components/Modal';
import { useState } from 'react';
import { useGetCustomCodeUploadEvents } from '../../api/events/events';
import { Spinner } from '@components/Spinner';

interface ActivityLogEntriesProps {
  filteredLogEntries: AuditEvent[];
}

export function ActivityLogEntries({
  filteredLogEntries,
}: ActivityLogEntriesProps) {
  const nameHeader = 'Name';
  const conditionHeader = 'Condition';
  const actionHeader = 'Action';
  const dateHeader = 'Date';

  const formatDatetime = useDatetimeFormatter();

  return (
    <Table striped fullWidth>
      <thead>
        <tr>
          <th scope="col">{nameHeader} </th>
          <th scope="col">{conditionHeader} </th>
          <th scope="col">{actionHeader}</th>
          <th scope="col">{dateHeader}</th>
        </tr>
      </thead>
      <tbody>
        {filteredLogEntries
          .sort((a, b) => (a.created_at > b.created_at ? -1 : 1))
          .map((r) => {
            const { date, time } = formatDatetime(r.created_at);
            return (
              <tr key={r.id} aria-label="Log entry">
                <td
                  data-label={nameHeader}
                  className="text-gray-cool-90! font-bold! break-all"
                >
                  {r.username}
                </td>
                <td data-label={conditionHeader}>
                  <div className="flex flex-col gap-1">
                    <span className="text-gray-cool-90!">
                      {r.configuration_name}
                    </span>
                    <span className="text-gray-cool-60!">
                      Version {r.configuration_version}
                    </span>
                  </div>
                </td>
                <td className="text-gray-cool-90!" data-label={actionHeader}>
                  <p className="flex flex-col items-start gap-1">
                    <span>{r.action_text}</span>
                    {r.has_custom_code_upload_events ? (
                      <ViewAllCustomCodeEventsButton
                        eventId={r.id}
                        importedByUsername={r.username}
                        importDate={date}
                      />
                    ) : null}
                  </p>
                </td>
                <td data-label={dateHeader}>
                  <div className="flex flex-col">
                    <span>{date}</span>
                    <span>{time}</span>
                  </div>
                </td>
              </tr>
            );
          })}
      </tbody>
    </Table>
  );
}

interface ViewAllCustomCodeEventsButtonProps {
  eventId: string;
  importedByUsername: string;
  importDate: string;
}

function ViewAllCustomCodeEventsButton({
  eventId,
  importedByUsername,
  importDate,
}: ViewAllCustomCodeEventsButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const {
    data: events,
    isError,
    isPending,
  } = useGetCustomCodeUploadEvents(eventId, {
    query: {
      enabled: isOpen,
    },
  });

  return (
    <>
      <Button
        className="p-0!"
        variant="tertiary"
        onClick={() => setIsOpen(true)}
      >
        View all
      </Button>
      <Modal open={isOpen} onClose={() => setIsOpen(false)}>
        <ModalHeader>
          <ModalTitle>Custom codes</ModalTitle>
        </ModalHeader>
        <ModalBody>
          {isPending ? (
            <Spinner />
          ) : isError ? (
            <p className="text-state-error">
              An error has occurred. Please refresh the page and try again.
            </p>
          ) : (
            <div className="flex max-h-130 flex-col gap-6">
              <p>
                Imported by {importedByUsername} on {importDate}
              </p>
              <div className="overflow-auto">
                {events.data.length === 0 ? (
                  <p>No custom code events found.</p>
                ) : (
                  <table className="w-full table-fixed">
                    <thead>
                      <tr className="border-gray-cool-20 text-gray-cool-90 border-b">
                        <th scope="col">Code system</th>
                        <th scope="col">Code</th>
                        <th scope="col" className="py-3">
                          Display name
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-gray-cool-20 divide-y">
                      {events.data.map((cc) => (
                        <tr key={cc.id}>
                          <td>{cc.system_display_name}</td>
                          <td>{cc.code}</td>
                          <td className="py-3">{cc.name}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}
        </ModalBody>
      </Modal>
    </>
  );
}
