import { useGetEvents } from '../../api/events/events';
import { Spinner } from '../../components/Spinner';
import Table from '../../components/Table';
import { Title } from '../../components/Title';
import ErrorFallback from '../ErrorFallback';

export function ActivityLog() {
  // will replace this with the actual API hook call once complete
  const { data: response, isPending, isError, error } = useGetEvents();
  const timeFormatter = new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: 'numeric',
    hour12: true,
  });

  if (isPending) return <Spinner variant="centered" />;
  if (isError) return <ErrorFallback error={error} />;

  return (
    <section className="mx-auto">
      <div className="mt-10">
        <Title>Activity log</Title>
        <p className="mt-2">
          Review activity in eCR Refiner from yourself and others on the team.
        </p>
      </div>

      <div className="mt-6">
        <Table striped>
          <colgroup>
            <col className="w-[16.5%]" />
            <col className="w-[23.5%]" />
            <col className="w-[48.5%]" />
            <col className="w-[11.5%]" />
          </colgroup>
          <thead>
            <tr>
              <th scope="col">Name </th>
              <th scope="col">Condition </th>
              <th scope="col">Action </th>
              <th scope="col">Date</th>
            </tr>
          </thead>

          <tbody>
            {response?.data
              .sort((a, b) => (a.created_at > b.created_at ? -1 : 1))
              .map((r) => {
                const createdAtDate = new Date(r.created_at);
                return (
                  <tr key={r.id}>
                    <td className="!font-bold">{r.username}</td>
                    <td>{r.configuration_name}</td>
                    <td>{r.action_text}</td>
                    <td>
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
