import { AuditEvent } from '../../api/schemas';
import {
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
} from '@components/Table';
import { useDatetimeFormatter } from '../../hooks/UseDatetimeFormatter';
import { Button } from '@components/Button';
import { Modal, ModalBody, ModalHeader, ModalTitle } from '@components/Modal';
import { useState } from 'react';
import { useGetCustomCodeUploadEvents } from '../../api/events/events';
import { Spinner } from '@components/Spinner';
import { useNavigate } from 'react-router';

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
  const navigate = useNavigate();

  return (
    <Table className="legacy-table legacy-table--striped table-auto">
      <TableHead>
        <TableRow>
          <TableHeaderCell className="text-gray-cool-90 w-[16%]">
            {nameHeader}
          </TableHeaderCell>
          <TableHeaderCell className="text-gray-cool-90 w-[22%]">
            {conditionHeader}
          </TableHeaderCell>
          <TableHeaderCell className="text-gray-cool-90 w-[46%]">
            {actionHeader}
          </TableHeaderCell>
          <TableHeaderCell className="text-gray-cool-90 w-[16%]">
            {dateHeader}
          </TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {filteredLogEntries
          .sort((a, b) => (a.created_at > b.created_at ? -1 : 1))
          .map((r) => {
            const { date, time } = formatDatetime(r.created_at);
            return (
              <TableRow key={r.id} aria-label="Log entry">
                <TableCell
                  data-label={nameHeader}
                  className="text-gray-cool-90! font-bold! break-all"
                >
                  {r.username}
                </TableCell>
                <TableCell data-label={conditionHeader}>
                  <div className="flex flex-col gap-1">
                    <span className="text-gray-cool-90!">
                      {r.configuration_name}
                    </span>
                    <span className="text-gray-cool-60!">
                      Version {r.configuration_version}
                    </span>
                  </div>
                </TableCell>
                <TableCell
                  className="text-gray-cool-90!"
                  data-label={actionHeader}
                >
                  <div className="flex flex-col items-start gap-1">
                    <div className="flex items-center gap-2">
                      <span>
                        {r.action_text}
                        {r.code_count != null
                          ? ` (${r.code_count.toLocaleString()} codes)`
                          : null}
                      </span>

                      {r.condition_id && r.code_count != null ? (
                        <CodeSetExportLink eventId={r.id} />
                      ) : null}
                    </div>

                    {r.has_custom_code_upload_events ? (
                      <ViewAllCustomCodeEventsButton
                        eventId={r.id}
                        modifiedByUsername={r.username}
                        modifiedDate={date}
                      />
                    ) : null}

                    {r.event_type === 'tes_update_existing_draft' ||
                    r.event_type === 'tes_create_draft_from_active' ? (
                      <Button
                        className="p-0!"
                        variant="tertiary"
                        onClick={() => navigate('/tes-updates')}
                      >
                        View updates
                      </Button>
                    ) : null}
                  </div>
                </TableCell>
                <TableCell data-label={dateHeader}>
                  <div className="flex flex-col">
                    <span className="text-gray-cool-60">{date}</span>
                    <span className="text-gray-cool-60">{time}</span>
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
      </TableBody>
    </Table>
  );
}

interface ViewAllCustomCodeEventsButtonProps {
  eventId: string;
  modifiedByUsername: string;
  modifiedDate: string;
}

function ViewAllCustomCodeEventsButton({
  eventId,
  modifiedByUsername,
  modifiedDate,
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
                Modified by {modifiedByUsername} on {modifiedDate}
              </p>
              <div className="overflow-auto">
                {events.data.length === 0 ? (
                  <p>No custom code events found.</p>
                ) : (
                  <Table className="w-full table-fixed">
                    <TableHead>
                      <TableRow className="border-gray-cool-20 text-gray-cool-90 border-b">
                        <TableHeaderCell>Code system</TableHeaderCell>
                        <TableHeaderCell>Code</TableHeaderCell>
                        <TableHeaderCell className="py-3">
                          Display name
                        </TableHeaderCell>
                      </TableRow>
                    </TableHead>
                    <TableBody className="divide-gray-cool-20 divide-y">
                      {events.data.map((cc) => (
                        <TableRow key={cc.id}>
                          <TableCell>{cc.system_display_name}</TableCell>
                          <TableCell>{cc.code}</TableCell>
                          <TableCell className="py-3">{cc.name}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </div>
            </div>
          )}
        </ModalBody>
      </Modal>
    </>
  );
}

interface CodeSetExportLinkProps {
  eventId: string;
}

function CodeSetExportLink({ eventId }: CodeSetExportLinkProps) {
  return (
    <Button
      className="p-0!"
      variant="tertiary"
      href={`/api/v1/events/${eventId}/codes/export`}
      anchorProps={{ download: true }}
    >
      <span className="whitespace-nowrap">Export as CSV</span>
    </Button>
  );
}
