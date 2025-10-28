import { Table } from '@trussworks/react-uswds';
import { Title } from '../../components/Title';

export function ActivityLog() {
  const data = [
    {
      message: 'some long description of the action',
      user: 'Someone Interesting',
      action: 'Something Interesting',
      date: new Date(),
    },
    {
      message: 'some long description of the action',
      user: 'Someone Interesting',
      action: 'Something Interesting',
      date: new Date(),
    },
    {
      message: 'some long description of the action',
      user: 'Someone Interesting',
      action: 'Something Interesting',
      date: new Date(),
    },
    {
      message: 'some long description of the action',
      user: 'Someone Interesting',
      action: 'Something Interesting',
      date: new Date(),
    },
  ];

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
            {data.map((r) => (
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
