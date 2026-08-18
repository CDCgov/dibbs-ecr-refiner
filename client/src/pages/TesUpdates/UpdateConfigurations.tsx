import { Table } from '@components/Table';
import { Title } from '@components/Title';
import { useGetConfigurationsToUpdate } from '../../api/tes/tes';

export function UpdateConfigurations() {
  const {
    data: response,
    isPending,
    isError,
  } = useGetConfigurationsToUpdate({ cur_tes_version: '6.0.0' });

  console.log(response);
  return (
    <div>
      <div className="bg-blue-cool-70 -mx-20 -mt-8 mb-8 px-20 py-3 text-white">
        {'Tes Updates > Updates'}{' '}
      </div>
      <Title className="pb-4">Update configurations</Title>
      <h2 className="text-[1.25rem]">Update to latest release</h2>
      <p>
        Update existing drafts and/or create a for existing configurations to
        apply the latest TES release. Drafts will need to be activated in order
        to receive the most up to date eCRs.
      </p>

      <Table fullWidth>
        <thead>
          <tr>
            <th scope="col" className="bg-white!">
              Configuration
            </th>
            <th scope="col" className="bg-white!">
              Current TES version
            </th>
            <th scope="col" className="bg-white!">
              Code sets
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>blah</td>
            <td>blah</td>
            <td>blah</td>
          </tr>
        </tbody>
      </Table>
    </div>
  );
}
