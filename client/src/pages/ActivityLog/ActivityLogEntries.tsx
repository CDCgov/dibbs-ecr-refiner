import { AuditEvent } from '../../api/schemas';
import { Table } from '../../components/Table';
import { useDatetimeFormatter } from '../../hooks/UseDatetimeFormatter';
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
    <Table striped>
      <colgroup>
        <col className="w-full sm:w-1/6" />
        <col className="w-2/6" />
        <col className="w-2/6" />
        <col className="w-1/6" />
      </colgroup>
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
                  className="text-gray-cool-90! font-bold!"
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
                  {r.action_text}
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
