import { useGetEvents } from '../../api/events/events';
import { Spinner } from '../../components/Spinner';
import Table from '../../components/Table';
import { Title } from '../../components/Title';
import ErrorFallback from '../ErrorFallback';

export function ActivityLog() {
  const { data: response, isPending, isError, error } = useGetEvents();
  const timeFormatter = new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: 'numeric',
    hour12: true,
  });

  if (isPending) return <Spinner variant="centered" />;
  if (isError) return <ErrorFallback error={error} />;

  const nameHeader = 'Name';
  const conditionHeader = 'Condition';
  const actionHeader = 'Action';
  const dateHeader = 'Date';

  return (
    <section className="mx-auto p-4">
      <div className="mt-10">
        <Title>Activity log</Title>
        <p className="mt-2">
          Review activity in eCR Refiner from yourself and others on the team.
        </p>
      </div>

      <div className="mt-6">
        <Table striped>
          <colgroup>
            <col className="w-full sm:w-1/4" />
            <col className="w-1/8" />
            <col className="w-1/2" />
            <col className="w-1/8" />
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
            {response?.data
              .sort((a, b) => (a.created_at > b.created_at ? -1 : 1))
              .map((r) => {
                const createdAtDate = new Date(r.created_at);
                return (
                  <tr key={r.id}>
                    <td data-label={nameHeader} className="!font-bold">
                      {r.username}
                    </td>
                    <td data-label={conditionHeader}>{r.configuration_name}</td>
                    <td data-label={actionHeader}>{r.action_text}</td>
                    <td data-label={dateHeader}>
                      {createdAtDate.toLocaleDateString()} <br />
                      {timeFormatter.format(createdAtDate)}
                    </td>
                  </tr>
                );
              })}
          </tbody>
        </Table>
      </div>
    </section>
  );
}
