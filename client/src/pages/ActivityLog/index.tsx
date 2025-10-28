import { Table } from '@trussworks/react-uswds';
import { Title } from '../../components/Title';

const NOW = new Date();
const stubbedData = [
  {
    message: 'some long description of the action',
    user: 'Someone Interesting',
    action: 'Something Interesting',
    date: new Date(NOW.setMinutes(NOW.getMinutes() - Math.random() * 10)), // add some variation
  },
  {
    message: 'some long description of the action',
    user: 'Someone Interesting',
    action: 'Something Interesting',
    date: new Date(NOW.setMinutes(NOW.getMinutes() - Math.random() * 10)),
  },
  {
    message: 'some long description of the action',
    user: 'Someone Interesting',
    action: 'Something Interesting',
    date: new Date(NOW.setMinutes(NOW.getMinutes() - Math.random() * 10)),
  },
  {
    message: 'some long description of the action',
    user: 'Someone Interesting',
    action: 'Something Interesting',
    date: NOW,
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
              .sort((a, b) => (a.date > b.date ? -1 : 1))
              .map((r) => (
                <tr>
                  <td className="!font-bold">{r.user}</td>
                  <td>{r.action}</td>
                  <td>{r.message}</td>
                  <td>
                    {r.date.toLocaleDateString()} <br />
                    {timeFormatter.format(r.date)}
                  </td>
                </tr>
              ))}
          </tbody>
        </Table>
      </div>
    </section>
  );
}
