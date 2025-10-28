import Table from '../../components/Table';
import { Title } from '../../components/Title';

interface ActivityEntry {
  id: string;
  username: string;
  configuration_name: string;
  action_text: string;
  created_at: string;
}
const stubbedData: ActivityEntry[] = [
  {
    id: 'fa74c1b3-a4e3-42eb-a350-c606083b5c5f',
    username: 'refiner',
    configuration_name: 'Alpha-gal Syndrome',
    action_text: 'Created configuration',
    created_at: '2025-10-28T13:58:45.363325Z',
  },
  {
    id: '10e1286d-487e-4f81-bee4-4c6d4df9ed92',
    username: 'refiner',
    configuration_name: 'Acanthamoeba',
    action_text: 'Created configuration',
    created_at: '2025-10-28T13:57:55.627842Z',
  },
];

export function ActivityLog() {
  // will replace this with the actual API hook call once complete
  const data = stubbedData;
  const timeFormatter = new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: 'numeric',
    hour12: true,
  });

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
            {data
              .sort((a, b) => (a.created_at > b.created_at ? -1 : 1))
              .map((r) => {
                const createdAtDate = new Date(r.created_at);
                return (
                  <tr>
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
